"""Multi-provider LLM client — BYOK (Bring Your Own Key) support.

Supports: Groq (default/free), OpenAI, Anthropic, Google Gemini, Together AI, OpenRouter.
`resolve_fields()` is the only entry point the planner uses.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import httpx

from ..config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL
from ..schemas import Element
from .budgeter import breaker, budgeter
from .prompt import SYSTEM, build_user_prompt

logger = logging.getLogger(__name__)

# ── Provider registry ──────────────────────────────────────────────────────────

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.1-8b-instant",
        "format": "openai",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "format": "openai",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-sonnet-4-20250514",
        "format": "anthropic",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-2.0-flash",
        "format": "google",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Llama-3-8b-chat-hf",
        "format": "openai",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "meta-llama/llama-3.1-8b-instruct:free",
        "format": "openai",
    },
}

# ── User config (set via PUT /api/config) ──
_user_config: dict[str, str] = {
    "provider": "groq",
    "api_key": "",
    "model": "",
}


def set_user_config(provider: str, api_key: str, model: str) -> None:
    global _user_config
    _user_config = {
        "provider": provider or "groq",
        "api_key": api_key or "",
        "model": model or "",
    }
    logger.info(f"LLM config updated: provider={provider}, model={model or '(default)'}, key={'***' + api_key[-4:] if api_key else '(none)'}")


def get_user_config() -> dict[str, str]:
    return {**_user_config, "api_key": "***" + _user_config["api_key"][-4:] if _user_config["api_key"] else ""}


def _active_config() -> tuple[str, str, str, str]:
    """Return (base_url, api_key, model, format). Users MUST provide their own key."""
    p = _user_config["provider"]
    prov = PROVIDERS.get(p, PROVIDERS["groq"])
    api_key = _user_config["api_key"]
    model = _user_config["model"] or prov["default_model"]
    base_url = prov["base_url"]
    fmt = prov["format"]
    return base_url, api_key, model, fmt


def has_api_key() -> bool:
    """Check if the user has configured an API key."""
    return bool(_user_config["api_key"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class RetryConfig:
    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    MAX_DELAY = 8.0
    BACKOFF_FACTOR = 2.0

    @classmethod
    def get_delay(cls, attempt: int) -> float:
        delay = cls.BASE_DELAY * (cls.BACKOFF_FACTOR ** attempt)
        return min(delay, cls.MAX_DELAY)


class LLMUnavailable(Exception):
    pass


class ErrorClassification:
    TRANSIENT = ["timeout", "connection", "429", "500", "502", "503", "504"]
    PERMANENT = ["401", "403", "invalid_api_key", "model_not_found"]

    @classmethod
    def is_transient(cls, error: Exception) -> bool:
        err_str = str(error).lower()
        if any(t in err_str for t in cls.TRANSIENT):
            return True
        if isinstance(error, (httpx.TimeoutException, httpx.ConnectError)):
            return True
        return False


def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content[content.find("{"):]
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in LLM response")
    return json.loads(content[start : end + 1])


# ── Provider-specific API calls ────────────────────────────────────────────────

def _call_openai_format(base_url: str, api_key: str, model: str,
                        system: str, user_content: Any) -> dict:
    """OpenAI-compatible API (works for Groq, OpenAI, Together, OpenRouter)."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "max_tokens": 600,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
    return resp.status_code, resp.json()


def _call_anthropic(api_key: str, model: str, system: str, user_content: str) -> tuple[int, dict]:
    """Anthropic Messages API."""
    payload = {
        "model": model,
        "max_tokens": 600,
        "system": system,
        "messages": [{"role": "user", "content": user_content}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
    data = resp.json()
    # Normalize to OpenAI-like structure
    if resp.status_code == 200 and "content" in data:
        text = data["content"][0]["text"] if data["content"] else ""
        data = {"choices": [{"message": {"content": text}}],
                "usage": {"total_tokens": data.get("usage", {}).get("input_tokens", 0) +
                          data.get("usage", {}).get("output_tokens", 0)}}
    return resp.status_code, data


def _call_google(api_key: str, model: str, system: str, user_content: str) -> tuple[int, dict]:
    """Google Gemini API."""
    payload = {
        "contents": [{"parts": [{"text": f"{system}\n\n{user_content}"}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 600,
                             "responseMimeType": "application/json"},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload)
    data = resp.json()
    # Normalize
    if resp.status_code == 200 and "candidates" in data:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        data = {"choices": [{"message": {"content": text}}],
                "usage": {"total_tokens": estimate_tokens(system + user_content + text)}}
    return resp.status_code, data


# ── Main entry point ───────────────────────────────────────────────────────────

def resolve_fields(profile_slice: str, elements: list[Element],
                   screenshot: Optional[str] = None) -> dict[str, dict]:
    """Ask the LLM to fill unresolved fields. Returns {element_id: {value, needs_user, confidence}}."""
    if not elements:
        return {}

    base_url, api_key, model, fmt = _active_config()

    if not api_key:
        logger.warning("No API key configured (set GROQ_API_KEY or use BYOK in settings)")
        return {}
    if breaker.is_open:
        logger.info("Circuit breaker open, skipping LLM call")
        return {}

    user_prompt = build_user_prompt(profile_slice, elements)
    prompt_tokens = estimate_tokens(SYSTEM + user_prompt)
    needed = prompt_tokens + 600

    # Budget check (only for Groq free tier)
    if fmt == "openai" and base_url == PROVIDERS["groq"]["base_url"]:
        wait = budgeter.seconds_until_fits(needed)
        if wait > 0:
            if wait > 20:
                logger.warning(f"Budget wait too long ({wait}s), deferring to ask_user")
                return {}
            time.sleep(wait)

    user_content: Any = user_prompt

    # Vision support (Groq only for now)
    if screenshot and fmt == "openai" and "groq" in base_url:
        model = "llama-3.2-90b-vision-preview"
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": screenshot}},
        ]

    last_error: Optional[Exception] = None
    for attempt in range(RetryConfig.MAX_RETRIES):
        try:
            # Call the appropriate provider
            if fmt == "anthropic":
                status_code, data = _call_anthropic(api_key, model, SYSTEM, user_prompt)
            elif fmt == "google":
                status_code, data = _call_google(api_key, model, SYSTEM, user_prompt)
            else:
                status_code, data = _call_openai_format(base_url, api_key, model, SYSTEM, user_content)

            if status_code == 429:
                logger.warning(f"Rate limited (429), attempt {attempt + 1}/{RetryConfig.MAX_RETRIES}")
                breaker.record_failure()
                budgeter.record(needed)
                if attempt < RetryConfig.MAX_RETRIES - 1:
                    time.sleep(RetryConfig.get_delay(attempt))
                    continue
                return {}

            if status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"HTTP {status_code}", request=None, response=None  # type: ignore
                )

            usage = data.get("usage", {})
            used = usage.get("total_tokens", needed)
            budgeter.record(used)

            content = data["choices"][0]["message"]["content"]
            parsed = _extract_json(content)
            breaker.record_success()

            out: dict[str, dict] = {}
            for ans in parsed.get("answers", []):
                if "id" in ans:
                    out[str(ans["id"])] = {
                        "value": ans.get("value"),
                        "needs_user": bool(ans.get("needs_user", False)),
                        "confidence": float(ans.get("confidence", 0.5)),
                    }

            logger.info(f"LLM ({_user_config['provider']}/{model}) resolved {len(out)} fields")
            return out

        except Exception as e:
            last_error = e
            is_transient = ErrorClassification.is_transient(e)
            logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}, transient={is_transient}")

            if not is_transient:
                breaker.record_failure()
                return {}

            if attempt < RetryConfig.MAX_RETRIES - 1:
                time.sleep(RetryConfig.get_delay(attempt))
            else:
                logger.error(f"Max retries exceeded: {last_error}")
                breaker.record_failure()

    return {}
