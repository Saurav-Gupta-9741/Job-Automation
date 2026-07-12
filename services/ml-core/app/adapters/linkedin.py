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

        # 0) Check for "already applied" / success confirmation
        already_applied_markers = [
            "you applied", "application submitted", "already applied",
            "view application", "application sent", "application complete",
            "your application was sent", "application submitted on",
            "you've already applied", "applied on",
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

        # 2) Look for resume upload prompt (LinkedIn may ask to upload a resume)
        resume_upload = _find_resume_upload(els)
        if resume_upload:
            return [Action(type=ActionType.UPLOAD_RESUME, target_id=resume_upload.id)]

        # 3) In the modal: first fill everything we can from the profile.
        fills = fill_known_fields(els, profile)
        if fills:
            return fills

        # 4) Handle LinkedIn custom radio buttons / checkboxes that aren't filled
        radio_action = _handle_radio_buttons(els, profile)
        if radio_action:
            return radio_action

        # 5) Unresolved REQUIRED fields remain -> defer to memory/LLM layer.
        #    Optional fields can be left empty — they won't block form submission.
        if unresolved_fields(els, profile, required_only=True):
            return None

        # 6) Everything on this screen is filled. Decide advance vs submit.
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

        # 7) "Review" button (LinkedIn sometimes has a separate review step)
        review = find_button(els, ["review"])
        if review:
            return [Action(type=ActionType.CLICK, target_id=review.id)]

        # 8) Success/confirmation screen -> done.
        if _looks_done(els):
            return [Action(type=ActionType.DONE)]

        dismiss = find_button(els, ["done", "dismiss", "not now"])
        if dismiss:
            return [Action(type=ActionType.DONE)]

        # Nothing actionable recognized -> let the planner try other layers.
        return None


def _modal_present(els: list[Element]) -> bool:
    """Detect if we're inside the Easy Apply modal."""
    # Strategy 1: Modal-specific buttons (Next, Submit, Review, Save)
    modal_buttons = NEXT_WORDS + SUBMIT_WORDS + ["review", "save and continue",
                                                   "upload resume", "choose resume"]
    if find_button(els, modal_buttons):
        return True

    # Strategy 2: Look for a dismiss/close button (modal always has one)
    if find_button(els, ["dismiss", "discard"]):
        return True

    # Strategy 3: Presence of screening-question fields
    screening_markers = ['phone', 'email', 'resume', 'experience', 'sponsorship',
                        'years', 'work authorization', 'salary', 'cover letter',
                        'how many years', 'are you legally', 'do you have',
                        'willing to relocate', 'notice period', 'current ctc',
                        'expected ctc', 'gender', 'disability', 'veteran']
    field_count = 0
    for e in els:
        if e.tag in ('input', 'select', 'textarea'):
            text = (e.text or e.placeholder or e.name or '').lower()
            if any(marker in text for marker in screening_markers):
                field_count += 1
                if field_count >= 2:
                    return True

    return False


def _looks_done(els: list[Element]) -> bool:
    """Check if we're on the post-submit success screen."""
    done_markers = [
        "application sent", "your application was sent",
        "application submitted", "you applied",
        "application complete", "thanks for applying",
    ]
    for e in els:
        t = text_of(e)
        if any(marker in t for marker in done_markers):
            return True
    return False


def _find_resume_upload(els: list[Element]) -> Optional[Element]:
    """Find a file input for resume upload."""
    for e in els:
        if e.tag == "input" and e.type == "file":
            label = text_of(e)
            if any(w in label for w in ["resume", "cv", "upload"]):
                return e
    return None


def _handle_radio_buttons(els: list[Element], profile: Profile) -> Optional[list[Action]]:
    """Handle LinkedIn's radio-button screening questions (Yes/No, etc)."""
    for e in els:
        if e.tag == "input" and e.type in ("radio", "checkbox"):
            if e.checked is False:
                label = text_of(e)
                val = profile.answer_for(label)
                if val is not None:
                    # Match the radio value to the profile answer
                    if val.lower() in ("yes", "true", "1") and "yes" in label.lower():
                        return [Action(type=ActionType.CLICK, target_id=e.id)]
                    if val.lower() in ("no", "false", "0") and "no" in label.lower():
                        return [Action(type=ActionType.CLICK, target_id=e.id)]
    return None
