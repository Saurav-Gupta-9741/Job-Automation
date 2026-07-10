"""The deterministic-first planner pipeline — the heart of Career OS.

Cascade, stopping at the first layer that yields an action:
  0. Safety     — blocker detection (CAPTCHA/OTP/OAuth), anti-loop, idempotency.
  1. Adapter    — platform rules (LinkedIn state machine / generic ATS).
  2. Memory     — Answer Bank recall for fields the adapter left unresolved.
  3. LLM        — Groq fallback for still-unresolved fields; caches answers back.
  4. ask_user   — anything left needs the human; hand off and resume later.
"""
from __future__ import annotations

import re
from typing import Optional

from ..config import REVIEW_BEFORE_SUBMIT
from ..llm import client as llm
from ..resume.profile import Profile, load_profile
from ..schemas import Action, ActionType, Element, StepRequest, StepResponse
from .. import storage, telemetry
from .router import route

# Words that signal an unsolvable-by-bot blocker -> hand to the human.
_BLOCKER_SIGNS = {
    "captcha": ["captcha", "recaptcha", "hcaptcha", "i'm not a robot",
                "verify you are human", "cloudflare"],
    "otp": ["one-time", "otp", "verification code", "enter the code",
            "6-digit", "sms code"],
    "oauth": ["sign in with google", "continue with google",
              "sign in with linkedin", "continue with linkedin"],
    "rate_limit": ["slow down", "too many applications", "wait a moment",
                   "you're applying too fast", "take a break",
                   "unusual activity", "verify your account",
                   "you've reached your application limit"],
}

MAX_STAGE_REPEATS = 3


def _detect_blocker(elements: list[Element]) -> Optional[tuple[str, str]]:
    blob = " ".join((e.text or "") + " " + (e.placeholder or "")
                    for e in elements).lower()
    for kind, signs in _BLOCKER_SIGNS.items():
        if any(s in blob for s in signs):
            if kind == "captcha":
                return kind, "A CAPTCHA needs solving. Solve it, then tap Resume."
            if kind == "otp":
                return kind, "Enter the verification code sent to you."
            if kind == "oauth":
                return kind, "Log in with the provider, then tap Resume."
    return None


def plan_step(req: StepRequest) -> StepResponse:
    profile = load_profile()
    storage.upsert_application(req.session_id, url=req.url, title=req.title)

    # --- Layer 0: safety -------------------------------------------------------
    # Idempotency: never act again on an already-submitted application.
    if storage.is_already_submitted(req.session_id):
        telemetry.track_completion(req.session_id, 0)  # Already done
        return _resp(req, [Action(type=ActionType.DONE)], "safety",
                     "already submitted", stage="done")

    # If the user just answered a handoff, persist it before planning.
    if req.user_input:
        _absorb_user_input(req)

    # Blocker detection (skip if the user just resolved one this step).
    blocker = _detect_blocker(req.elements)
    if blocker and not (req.user_input and req.user_input.get("resumed")):
        kind, msg = blocker
        telemetry.track_handoff(req.session_id, f"blocker: {kind}")
        return _resp(req, [Action(type=ActionType.ASK_USER, input_kind=_kind(kind),
                                  prompt=msg)],
                     "safety", f"blocker: {kind}", stage=f"handoff:{kind}")

    # Enhanced anti-loop with cycle detection
    if req.stage_hash:
        # Check for cyclic patterns first
        cycle = storage.detect_cycle_pattern(req.session_id, req.stage_hash)
        if cycle:
            storage.reset_stage(req.session_id, req.stage_hash)
            telemetry.track_loop(req.session_id, "cycle", cycle)
            telemetry.track_handoff(req.session_id, f"cycle: {cycle}")
            return _resp(req, [Action(
                type=ActionType.ASK_USER, input_kind="manual",
                prompt=f"Detected loop pattern ({cycle}). Please help me proceed, then tap Resume.",
            )], "safety", f"cycle detected: {cycle}", stage="handoff:cycle")
        
        # Track state transitions
        prev_hash = getattr(req, "_prev_stage_hash", None)
        if prev_hash and prev_hash != req.stage_hash:
            storage.record_state_transition(req.session_id, prev_hash, req.stage_hash)
        
        # Traditional counter-based loop detection as fallback
        count = storage.bump_stage(req.session_id, req.stage_hash)
        if count > MAX_STAGE_REPEATS:
            storage.reset_stage(req.session_id, req.stage_hash)
            telemetry.track_loop(req.session_id, "stuck", f"repeat count: {count}")
            telemetry.track_handoff(req.session_id, "stuck on step")
            return _resp(req, [Action(
                type=ActionType.ASK_USER, input_kind="manual",
                prompt="I'm stuck on this step. Please help me proceed, then tap Resume.",
            )], "safety", "anti-loop escalation", stage="handoff:stuck")

    # --- Layer 1: adapter rules ------------------------------------------------
    adapter = route(req.url)
    actions = adapter.plan(req, profile)
    if actions:
        _post_process_submit(req, actions)
        return _resp(req, actions, "rule", f"{adapter.name} rule", stage=adapter.name)

    # --- Layers 2+3: resolve leftover fields via memory, then LLM --------------
    unresolved = _unresolved(req, profile)
    if unresolved:
        actions, source = _resolve_fields(req, profile, unresolved)
        if actions:
            return _resp(req, actions, source, "resolved fields", stage=adapter.name)

    # --- Layer 4: nothing actionable -> ask the human --------------------------
    return _resp(req, [Action(
        type=ActionType.ASK_USER, input_kind="manual",
        prompt="I couldn't determine the next step. Please advance the form, then tap Resume.",
    )], "safety", "no deterministic action", stage="handoff:unknown")


# --- field resolution ----------------------------------------------------------

def _validate_answer(element: Element, value: str) -> tuple[bool, str]:
    """Validate that answer matches expected format for the field type."""
    if not value:
        return True, ""  # Empty is handled elsewhere
    
    label = (element.text or element.placeholder or element.name or "").lower()
    
    # Email validation
    if "email" in label or element.type == "email":
        if "@" not in value or "." not in value.split("@")[-1]:
            return False, f"Invalid email format: {value}"
    
    # Phone validation
    if "phone" in label or "mobile" in label or element.type == "tel":
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) < 10:
            return False, f"Phone number too short: {value}"
    
    # URL validation
    if any(word in label for word in ["website", "linkedin", "github", "portfolio", "url"]):
        if not re.match(r'^https?://', value) and not value.startswith("www."):
            return False, f"Invalid URL format: {value}"
    
    # Number validation
    if element.type == "number" or "salary" in label or "years" in label:
        try:
            float(value.replace(",", "").replace("$", ""))
        except ValueError:
            return False, f"Invalid number format: {value}"
    
    return True, ""


def _unresolved(req: StepRequest, profile: Profile) -> list[Element]:
    from ..adapters.base import unresolved_fields
    return unresolved_fields(req.elements, profile)


def _resolve_fields(req: StepRequest, profile: Profile,
                    unresolved: list[Element]) -> tuple[list[Action], str]:
    """Try Answer Bank first (0 tokens), then LLM for the remainder with confidence tiers."""
    fields: list[dict] = []
    still_unknown: list[Element] = []
    source = "memory"

    for e in unresolved:
        label = e.text or e.placeholder or e.name or ""
        hit = storage.recall_answer(label)
        if hit and hit["answer"]:
            telemetry.track_memory_hit(req.session_id, label)
            fields.append({"target_id": e.id, "value": hit["answer"],
                           "select": e.tag == "select"})
        else:
            still_unknown.append(e)

    if still_unknown:
        answers = llm.resolve_fields(profile.context_slice(), still_unknown)
        by_id = {e.id: e for e in still_unknown}
        needs_user: list[Element] = []
        low_confidence: list[Element] = []
        resolved_count = 0
        
        for eid, res in answers.items():
            e = by_id.get(eid)
            if not e:
                continue
            
            confidence = res.get("confidence", 0.5)
            value = res.get("value")
            needs_user_flag = res.get("needs_user", False)
            
            # Confidence tiers:
            # 0.85+: High confidence - auto-fill
            # 0.60-0.84: Medium confidence - fill but could flag for review
            # 0.40-0.59: Low confidence - pre-populate with warning or ask
            # <0.40: Very low - ask user
            
            if needs_user_flag or value in (None, "") or confidence < 0.40:
                needs_user.append(e)
                continue
            
            if confidence < 0.60:
                # Low confidence: still fill but track it
                low_confidence.append(e)
            
            source = "llm"
            resolved_count += 1
            
            # Validate the answer before using it
            is_valid, error_msg = _validate_answer(e, value)
            if not is_valid:
                # Log validation failure and ask user for correct value
                telemetry.track_error(req.session_id, "validation_failed", error_msg)
                needs_user.append(e)
                continue
            
            fields.append({"target_id": e.id, "value": value,
                           "select": e.tag == "select"})
            storage.remember_answer(e.text or e.placeholder or e.name or "",
                                    str(value), "llm", confidence)
        
        # Track LLM usage
        if resolved_count > 0:
            telemetry.track_llm_call(req.session_id, resolved_count, 0)  # tokens tracked elsewhere
        
        # Any element the LLM couldn't/shouldn't answer -> ask the user for it.
        unanswered = needs_user + [e for e in still_unknown
                                   if e.id not in answers]
        if unanswered and not fields:
            e = unanswered[0]
            label = e.text or e.placeholder or e.name or "this field"
            telemetry.track_handoff(req.session_id, f"unknown field: {label}")
            return [Action(type=ActionType.ASK_USER, input_kind="text",
                           prompt=f"Please answer: {label}", target_id=e.id)], "safety"

    if fields:
        return [Action(type=ActionType.FILL_ALL, fields=fields)], source
    return [], source


# --- handoff input + submit bookkeeping ---------------------------------------

def _absorb_user_input(req: StepRequest) -> None:
    """Persist answers the user provided during a handoff into the Answer Bank."""
    ui = req.user_input or {}
    # Confirm-to-submit handoff.
    if ui.get("confirmed_submit"):
        return  # handled in _post_process_submit via the follow-up step
    
    # Phase 6: Save implicitly learned fields from manual interaction pauses
    learned = ui.get("learned_fields")
    if learned and isinstance(learned, dict):
        for sig, val in learned.items():
            el = next((e for e in req.elements if e.signature == sig), None)
            if el:
                label = el.text or el.placeholder or el.name or ""
                if label:
                    storage.remember_answer(label, str(val), "user", 1.0)
                    
    # Free-text answer to a specific field/question.
    q = ui.get("question")
    a = ui.get("answer")
    if q and a:
        storage.remember_answer(str(q), str(a), "user", 1.0)


def _post_process_submit(req: StepRequest, actions: list[Action]) -> None:
    """Mark the application submitted when we emit an actual submit click."""
    for a in actions:
        if a.type == ActionType.DONE:
            storage.upsert_application(req.session_id, status="submitted", submitted=1)
        # A real (non-review) submit click also marks submitted.
        if (a.type == ActionType.CLICK and not REVIEW_BEFORE_SUBMIT
                and a.target_id and _is_submit_target(req, a.target_id)):
            storage.upsert_application(req.session_id, status="submitted", submitted=1)


def _is_submit_target(req: StepRequest, target_id: str) -> bool:
    from ..adapters.base import text_of, SUBMIT_WORDS
    for e in req.elements:
        if e.id == target_id and any(w in text_of(e) for w in SUBMIT_WORDS):
            return True
    return False


def _kind(blocker_kind: str) -> str:
    mapping = {
        "captcha": "manual",
        "otp": "otp",
        "oauth": "manual",
        "rate_limit": "manual"
    }
    return mapping.get(blocker_kind, "manual")


def _resp(req: StepRequest, actions: list[Action], source: str, reason: str,
          stage: str = "") -> StepResponse:
    return StepResponse(session_id=req.session_id, script=actions, source=source,
                        reason=reason, stage=stage, tokens_used=0)
