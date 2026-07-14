"""LinkedIn Easy Apply as an explicit state machine with structural detection.

Easy Apply is a finite modal flow. We detect the current stage from the visible elements
and emit the next deterministic action. Only genuinely novel screening questions fall
through (return None) to the memory/LLM layers. This keeps LinkedIn near-100% reliable and
almost token-free.

Enhanced with:
- Structural modal detection (not just text-based)
- Better radio/checkbox handling for complex questions
- Multi-page application support
- External redirect detection
- Dynamic content loading handling
"""
from __future__ import annotations

import re
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
        if self._is_already_applied(els):
            return [Action(type=ActionType.DONE)]

        # 1) Not in the modal yet: open Easy Apply.
        if not self._modal_present(els):
            easy = find_button(els, ["easy apply", "apply now"])
            if easy:
                return [Action(type=ActionType.CLICK, target_id=easy.id)]
            # No Easy Apply button -> external apply / unknown; defer to router+LLM.
            return None

        # 2) Check for external redirect (LinkedIn sometimes redirects to company site)
        if self._is_external_redirect(els):
            return [Action(
                type=ActionType.ASK_USER,
                input_kind="manual",
                prompt="Redirected to external site. Please complete the application there, then return and tap Resume.",
            )]

        # 3) Look for resume upload prompt (LinkedIn may ask to upload a resume)
        resume_upload = self._find_resume_upload(els)
        if resume_upload:
            return [Action(type=ActionType.UPLOAD_RESUME, target_id=resume_upload.id)]

        # 4) In the modal: first fill everything we can from the profile.
        fills = fill_known_fields(els, profile)
        if fills:
            return fills

        # 5) Handle LinkedIn custom radio buttons / checkboxes that aren't filled
        radio_action = self._handle_radio_buttons(els, profile)
        if radio_action:
            return radio_action

        # 6) Handle dropdown/select questions
        dropdown_action = self._handle_dropdowns(els, profile)
        if dropdown_action:
            return dropdown_action

        # 7) Unresolved REQUIRED fields remain -> defer to memory/LLM layer.
        #    Optional fields can be left empty — they won't block form submission.
        if unresolved_fields(els, profile, required_only=True):
            return None

        # 8) Everything on this screen is filled. Decide advance vs submit.
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

        # 9) "Review" button (LinkedIn sometimes has a separate review step)
        review = find_button(els, ["review", "review application"])
        if review:
            return [Action(type=ActionType.CLICK, target_id=review.id)]

        # 10) Success/confirmation screen -> done.
        if self._looks_done(els):
            return [Action(type=ActionType.DONE)]

        dismiss = find_button(els, ["done", "dismiss", "not now", "close"])
        if dismiss:
            return [Action(type=ActionType.DONE)]

        # Nothing actionable recognized -> let the planner try other layers.
        return None

    def _is_already_applied(self, els: list[Element]) -> bool:
        """Check if already applied to this job."""
        already_applied_markers = [
            "you applied", "application submitted", "already applied",
            "view application", "application sent", "application complete",
            "your application was sent", "application submitted on",
            "you've already applied", "applied on", "application received",
        ]
        for e in els:
            t = text_of(e).lower()
            if any(marker in t for marker in already_applied_markers):
                return True
        return False

    def _is_external_redirect(self, els: list[Element]) -> bool:
        """Detect if we've been redirected to an external career site."""
        # Look for signs we're no longer on LinkedIn's Easy Apply modal
        external_indicators = [
            "workday", "greenhouse", "lever", "icims", "taleo", "brassring",
            "successfactors", "oraclecloud", "sap", "bamboohr", "jobvite",
        ]
        url = getattr(self, '_current_url', '')
        for indicator in external_indicators:
            if indicator in url.lower():
                return True
        
        # Check for external site markers in page content
        for e in els:
            t = text_of(e).lower()
            if any(indicator in t for indicator in external_indicators):
                return True
        return False

    def _modal_present(self, els: list[Element]) -> bool:
        """Detect if we're inside the Easy Apply modal using structural cues."""
        # Strategy 1: Modal-specific buttons (Next, Submit, Review, Save)
        modal_buttons = NEXT_WORDS + SUBMIT_WORDS + ["review", "save and continue",
                                                       "upload resume", "choose resume",
                                                       "continue to apply"]
        if find_button(els, modal_buttons):
            return True

        # Strategy 2: Look for a dismiss/close button (modal always has one)
        if find_button(els, ["dismiss", "discard", "close", "cancel"]):
            return True

        # Strategy 3: Presence of screening-question fields (2+ fields)
        screening_markers = ['phone', 'email', 'resume', 'experience', 'sponsorship',
                            'years', 'work authorization', 'salary', 'cover letter',
                            'how many years', 'are you legally', 'do you have',
                            'willing to relocate', 'notice period', 'current ctc',
                            'expected ctc', 'gender', 'disability', 'veteran',
                            'linkedin', 'github', 'portfolio', 'website']
        field_count = 0
        for e in els:
            if e.tag in ('input', 'select', 'textarea'):
                text = (e.text or e.placeholder or e.name or '').lower()
                if any(marker in text for marker in screening_markers):
                    field_count += 1
                    if field_count >= 2:
                        return True

        # Strategy 4: Structural detection - look for modal container patterns
        # LinkedIn modals typically have specific ARIA roles or classes
        for e in els:
            # Check for modal-like containers
            if e.tag == 'div' and e.text:
                text_lower = e.text.lower()
                if any(kw in text_lower for kw in ['easy apply', 'apply to', 'application for']):
                    # Check if this looks like a modal header
                    if find_button(els, ["next", "submit", "review", "dismiss"]):
                        return True

        return False

    def _looks_done(self, els: list[Element]) -> bool:
        """Check if we're on the post-submit success screen."""
        done_markers = [
            "application sent", "your application was sent",
            "application submitted", "you applied",
            "application complete", "thanks for applying",
            "your application has been submitted", "congratulations",
            "follow", "done", "you've already applied", "already applied",
        ]
        for e in els:
            t = text_of(e).lower()
            if any(marker in t for marker in done_markers):
                return True
        return False

    def _find_resume_upload(self, els: list[Element]) -> Optional[Element]:
        """Find a file input for resume upload."""
        for e in els:
            if e.tag == "input" and e.type == "file":
                label = text_of(e)
                if any(w in label for w in ["resume", "cv", "upload", "attach"]):
                    return e
        return None

    def _handle_radio_buttons(self, els: list[Element], profile: Profile) -> Optional[list[Action]]:
        """Handle LinkedIn's radio-button screening questions (Yes/No, etc)."""
        for e in els:
            if e.tag == "input" and e.type in ("radio", "checkbox"):
                if e.checked is False:
                    label = text_of(e)
                    val = profile.answer_for(label)
                    if val is not None:
                        val_lower = val.lower()
                        label_lower = label.lower()
                        # Match the radio value to the profile answer
                        if val_lower in ("yes", "true", "1", "y") and any(w in label_lower for w in ["yes", "true", "agree", "confirm"]):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        if val_lower in ("no", "false", "0", "n") and any(w in label_lower for w in ["no", "false", "disagree", "decline"]):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        # Handle "Authorized to work" type questions
                        if "authoriz" in label_lower and val_lower in ("yes", "true", "1"):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        if "sponsor" in label_lower and val_lower in ("no", "false", "0"):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
        return None

    def _handle_dropdowns(self, els: list[Element], profile: Profile) -> Optional[list[Action]]:
        """Handle dropdown/select questions that profile can answer."""
        for e in els:
            if e.tag == "select" and e.options:
                label = text_of(e)
                val = profile.answer_for(label)
                if val is not None:
                    # Try to match the value to one of the options
                    for opt in e.options:
                        if val.lower() in opt.lower() or opt.lower() in val.lower():
                            return [Action(
                                type=ActionType.FILL_ALL,
                                fields=[{"target_id": e.id, "value": opt, "select": True}]
                            )]
        return None
