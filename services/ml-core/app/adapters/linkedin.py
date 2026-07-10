"""LinkedIn Easy Apply as an explicit state machine.

Easy Apply is a finite modal flow. We detect the current stage from the visible elements
and emit the next deterministic action. Only genuinely novel screening questions fall
through (return None) to the memory/LLM layers. This keeps LinkedIn near-100% reliable and
almost token-free.
"""
from __future__ import annotations

from typing import Optional

from ..config import REVIEW_BEFORE_SUBMIT
from ..resume.profile import Profile
from ..schemas import Action, ActionType, Element, StepRequest
from .base import (
    Adapter,
    NEXT_WORDS,
    SUBMIT_WORDS,
    fill_known_fields,
    find_button,
    text_of,
    unresolved_fields,
)


class LinkedInAdapter(Adapter):
    name = "linkedin"

    def matches(self, url: str) -> bool:
        return "linkedin.com" in url

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        els = req.elements

        # 0) Check for "already applied" state first
        already_applied_markers = [
            "you applied", "application submitted", "already applied",
            "view application", "application sent", "application submitted on",
            "your application was sent", "application complete"
        ]
        for e in els:
            t = text_of(e)
            if any(marker in t for marker in already_applied_markers):
                return [Action(type=ActionType.DONE)]

        # 1) Not in the modal yet: open Easy Apply.
        if not _modal_present(els):
            easy = find_button(els, ["easy apply"])
            if easy:
                return [Action(type=ActionType.CLICK, target_id=easy.id)]
            # No Easy Apply button -> external apply / unknown; defer to router+LLM.
            return None

        # 2) In the modal: first fill everything we can from the profile.
        fills = fill_known_fields(els, profile)
        if fills:
            return fills

        # 3) Unresolved fillable fields remain -> defer to memory/LLM layer.
        if unresolved_fields(els, profile):
            return None

        # 4) Everything on this screen is filled. Decide advance vs submit.
        submit = find_button(els, SUBMIT_WORDS)
        if submit:
            if REVIEW_BEFORE_SUBMIT:
                return [Action(
                    type=ActionType.ASK_USER,
                    input_kind="confirm",
                    prompt="Review the application, then confirm to submit.",
                    target_id=submit.id,
                )]
            return [Action(type=ActionType.CLICK, target_id=submit.id)]

        nxt = find_button(els, NEXT_WORDS)
        if nxt:
            return [Action(type=ActionType.CLICK, target_id=nxt.id)]

        # 5) Success/confirmation screen -> done.
        if _looks_done(els) or find_button(els, ["done", "dismiss"]):
            return [Action(type=ActionType.DONE)]

        # Nothing actionable recognized -> let the planner try other layers.
        return None


def _modal_present(els: list[Element]) -> bool:
    # Strategy 1: Look for modal-specific buttons
    if find_button(els, NEXT_WORDS + SUBMIT_WORDS + ["review", "save and continue"]):
        return True
    
    # Strategy 2: Presence of screening questions (common Easy Apply fields)
    screening_markers = ['phone', 'email', 'resume', 'experience', 'sponsorship',
                        'years', 'work authorization', 'salary']
    field_count = 0
    for e in els:
        if e.tag in ('input', 'select', 'textarea'):
            text = (e.text or e.placeholder or e.name or '').lower()
            if any(marker in text for marker in screening_markers):
                field_count += 1
                if field_count >= 2:  # At least 2 screening fields = likely in modal
                    return True
    
    return False


def _looks_done(els: list[Element]) -> bool:
    for e in els:
        t = text_of(e)
        if "application sent" in t or "your application was sent" in t:
            return True
    return False
