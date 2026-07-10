"""Groq client wrapper: budget-aware, circuit-broken, JSON-validated.

`resolve_fields()` is the only entry point the planner uses. It returns a dict of
element_id -> {value, needs_user, confidence}, or an empty dict when the LLM is
unavailable/over budget (the planner then falls back to ask_user).
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

# Rough token estimate: ~4 chars per token. Good enough for budgeting.
def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# Enhanced retry logic with exponential backoff
class RetryConfig:
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 8.0
    BACKOFF_FACTOR = 2.0
    
    @classmethod
    def get_delay(cls, attempt: int) -> float:
        """Calculate exponential backoff delay for given attempt."""
        delay = cls.BASE_DELAY * (cls.BACKOFF_FACTOR ** attempt)
        return min(delay, cls.MAX_DELAY)


class LLMUnavailable(Exception):
    pass


class ErrorClassification:
    """Classify errors to determine retry strategy."""
    TRANSIENT = ["timeout", "connection", "429", "500", "502", "503", "504"]
    PERMANENT = ["401", "403", "invalid_api_key", "model_not_found"]
    
    @classmethod
    def is_transient(cls, error: Exception) -> bool:
        """Determine if error is likely transient and worth retrying."""
        err_str = str(error).lower()
        if any(t in err_str for t in cls.TRANSIENT):
            return True
        if isinstance(error, httpx.TimeoutException):
            return True
        if isinstance(error, httpx.ConnectError):
            return True
        return False


def _extract_json(content: str) -> dict[str, Any]:
    """Groq usually returns clean JSON; strip stray fences/prose defensively."""
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content[content.find("{"):]
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in LLM response")
    return json.loads(content[start : end + 1])


def resolve_fields(profile_slice: str, elements: list[Element]) -> dict[str, dict]:
    """Ask the LLM to fill the given unresolved fields with enhanced retry logic."""
    if not elements:
        return {}
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not configured")
        return {}
    if breaker.is_open:
        logger.info("Circuit breaker open, skipping LLM call")
        return {}

    user_prompt = build_user_prompt(profile_slice, elements)
    prompt_tokens = estimate_tokens(SYSTEM + user_prompt)
    needed = prompt_tokens + 600

    wait = budgeter.seconds_until_fits(needed)
    if wait > 0:
        if wait > 20:
            logger.warning(f"Budget wait too long ({wait}s), deferring to ask_user")
            return {}
        time.sleep(wait)

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "max_tokens": 600,
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    # Enhanced retry logic with exponential backoff
    last_error: Optional[Exception] = None
    for attempt in range(RetryConfig.MAX_RETRIES):
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{GROQ_BASE_URL}/chat/completions", json=payload, headers=headers
                )
            
            if resp.status_code == 429:
                logger.warning(f"Rate limited (429), attempt {attempt + 1}/{RetryConfig.MAX_RETRIES}")
                breaker.record_failure()
                budgeter.record(needed)
                if attempt < RetryConfig.MAX_RETRIES - 1:
                    time.sleep(RetryConfig.get_delay(attempt))
                    continue
                return {}
            
            resp.raise_for_status()
            data = resp.json()

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
            
            logger.info(f"LLM resolved {len(out)} fields successfully")
            return out
            
        except Exception as e:
            last_error = e
            is_transient = ErrorClassification.is_transient(e)
            logger.warning(
                f"LLM call failed (attempt {attempt + 1}/{RetryConfig.MAX_RETRIES}): {e}, "
                f"transient={is_transient}"
            )
            
            if not is_transient:
                logger.error(f"Permanent error detected: {e}")
                breaker.record_failure()
                return {}
            
            # Retry transient errors with backoff
            if attempt < RetryConfig.MAX_RETRIES - 1:
                delay = RetryConfig.get_delay(attempt)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Max retries exceeded, last error: {last_error}")
                breaker.record_failure()
    
    return {}
