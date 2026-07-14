"""Greenhouse ATS: a single long application form on boards.greenhouse.io.

Enhanced with:
- Greenhouse-specific button vocabulary
- Resume upload handling
- EEO/demographic question handling
- Custom field detection
- Better submit detection
"""
from __future__ import annotations

from typing import Optional

from ..resume.profile import Profile
from ..schemas import Action, ActionType, StepRequest
from .generic import GenericATSAdapter, APPLY_WORDS
from .base import find_button, text_of, fill_known_fields, unresolved_fields


GREENHOUSE_APPLY_WORDS = ["apply for this job", "apply now", "apply", "submit application"]
GREENHOUSE_SUBMIT_WORDS = ["submit application", "submit", "send application", "apply now"]
GREENHOUSE_NEXT_WORDS = ["continue", "next", "review", "save and continue"]
GREENHOUSE_EEO_WORDS = ["eeo", "equal employment", "voluntary self-identification", 
                         "demographic", "gender", "race", "ethnicity", "veteran", "disability"]


class GreenhouseAdapter(GenericATSAdapter):
    name = "greenhouse"

    def matches(self, url: str) -> bool:
        u = url.lower()
        return "greenhouse.io" in u or "boards.greenhouse" in u or "grnh.se" in u

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        els = req.elements

        # 1) Check for "Apply for this job" reveal button (some Greenhouse boards)
        apply_btn = find_button(els, GREENHOUSE_APPLY_WORDS)
        if apply_btn:
            return [Action(type=ActionType.CLICK, target_id=apply_btn.id)]

        # 2) Check for resume upload
        resume_upload = self._find_resume_upload(els)
        if resume_upload:
            return [Action(type=ActionType.UPLOAD_RESUME, target_id=resume_upload.id)]

        # 3) Fill known fields from profile
        fills = fill_known_fields(els, profile)
        if fills:
            return fills

        # 4) Handle EEO/demographic questions (optional, can skip)
        eeo_action = self._handle_eeo_questions(els, profile)
        if eeo_action:
            return eeo_action

        # 5) Unresolved REQUIRED fields remain -> defer to memory/LLM layer
        if unresolved_fields(els, profile, required_only=True):
            return None

        # 6) Everything filled - look for submit
        submit = find_button(els, GREENHOUSE_SUBMIT_WORDS)
        if submit:
            return [Action(type=ActionType.CLICK, target_id=submit.id)]

        # 7) Multi-step: look for next/continue
        nxt = find_button(els, GREENHOUSE_NEXT_WORDS)
        if nxt:
            return [Action(type=ActionType.CLICK, target_id=nxt.id)]

        # 8) Success screen
        if self._looks_done(els):
            return [Action(type=ActionType.DONE)]

        return None

    def _find_resume_upload(self, els) -> Optional[object]:
        """Find a file input for resume upload."""
        for e in els:
            if e.tag == "input" and e.type == "file":
                label = text_of(e)
                if any(w in label for w in ["resume", "cv", "upload", "attach", "file"]):
                    return e
        return None

    def _handle_eeo_questions(self, els, profile: Profile) -> Optional[list[Action]]:
        """Handle Greenhouse's EEO/demographic questions (usually optional)."""
        for e in els:
            label = text_of(e).lower()
            if any(w in label for w in GREENHOUSE_EEO_WORDS):
                # These are typically optional - we can skip or answer from profile
                if e.tag == "select" and e.options:
                    val = profile.answer_for(label)
                    if val:
                        for opt in e.options:
                            if val.lower() in opt.lower() or opt.lower() in val.lower():
                                return [Action(
                                    type=ActionType.FILL_ALL,
                                    fields=[{"target_id": e.id, "value": opt, "select": True}]
                                )]
                elif e.tag == "input" and e.type in ("radio", "checkbox"):
                    val = profile.answer_for(label)
                    if val and val.lower() in ("yes", "true", "1", "y"):
                        return [Action(type=ActionType.CLICK, target_id=e.id)]
        return None

    def _looks_done(self, els) -> bool:
        """Check if we're on the post-submit success screen."""
        done_markers = [
            "application submitted", "thank you for applying",
            "your application has been received", "application received",
            "we received your application", "thanks for applying",
            "confirmation", "application complete"
        ]
        for e in els:
            t = text_of(e).lower()
            if any(marker in t for marker in done_markers):
                return True
        return False
