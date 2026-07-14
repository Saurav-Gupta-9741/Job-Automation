"""Workday ATS: a multi-page wizard on *.myworkdayjobs.com.

Workday is the hard one, with several quirks the generic flow doesn't know about:

  1. Account wall — most Workday tenants force "Create Account / Sign In" before applying.
     Credentials are the user's, so we hand off (ask_user) rather than guess.
  2. Multi-page wizard — advances via "Save and Continue" / "Next", one section per page.
     Our generic NEXT_WORDS already covers these; we add Workday's exact phrasing.
  3. Iframes — some tenants render the form in an iframe. The content script currently
     scans the top frame only; if we detect an empty top frame with a Workday shell, we
     ask the user to interact so we don't silently stall.
  4. Dynamic content — Workday heavily uses AJAX; we need to wait for content to load.
  5. Custom fields — each tenant can add custom screening questions.
  6. Resume parsing — Workday has built-in resume parsing; we should leverage it.
  7. Conditional fields — some fields appear based on previous answers.
"""
from __future__ import annotations

import re
from typing import Optional

from ..resume.profile import Profile
from ..schemas import Action, ActionType, StepRequest
from .generic import GenericATSAdapter
from .base import find_button, text_of, fill_known_fields, unresolved_fields

ACCOUNT_WALL_WORDS = ["create account", "sign in to apply", "create an account",
                      "sign in", "verify new password", "register", "log in", "login"]
AUTOFILL_WORDS = ["autofill with resume", "use my last application",
                  "autofill from resume", "parse resume", "upload resume"]
WORKDAY_NEXT_WORDS = ["save and continue", "continue", "next", "review", "submit"]
WORKDAY_SUBMIT_WORDS = ["submit", "submit application", "send application", "apply now"]


class WorkdayAdapter(GenericATSAdapter):
    name = "workday"

    def matches(self, url: str) -> bool:
        u = url.lower()
        return "myworkdayjobs.com" in u or "workday" in u or "wd1.myworkday" in u

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        els = req.elements

        # 0) Check if we're in an iframe context (empty top frame with Workday shell)
        if self._is_iframe_shell(els):
            return [Action(
                type=ActionType.ASK_USER, input_kind="manual",
                prompt="Workday form appears to be in an iframe. Please click into the form area, then tap Resume.",
            )]

        # 1) Prefer Workday's own "Autofill with Resume" — fastest, most accurate path.
        autofill = find_button(els, AUTOFILL_WORDS)
        if autofill:
            return [Action(type=ActionType.CLICK, target_id=autofill.id)]

        # 2) Check for resume upload prompt
        resume_upload = self._find_resume_upload(els)
        if resume_upload:
            return [Action(type=ActionType.UPLOAD_RESUME, target_id=resume_upload.id)]

        # 3) Account wall -> hand off (user's own credentials / verification email).
        if self._is_account_wall(els):
            return [Action(
                type=ActionType.ASK_USER, input_kind="manual",
                prompt="Workday needs you to create an account / sign in. Do that, then tap Resume.",
            )]

        # 4) Fill known fields from profile
        fills = fill_known_fields(els, profile)
        if fills:
            return fills

        # 5) Handle Workday-specific radio/checkbox questions
        radio_action = self._handle_radio_questions(els, profile)
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
        submit = find_button(els, WORKDAY_SUBMIT_WORDS)
        if submit:
            return [Action(type=ActionType.CLICK, target_id=submit.id)]

        nxt = find_button(els, WORKDAY_NEXT_WORDS)
        if nxt:
            return [Action(type=ActionType.CLICK, target_id=nxt.id)]

        # 9) Success/confirmation screen -> done.
        if self._looks_done(els):
            return [Action(type=ActionType.DONE)]

        # Nothing actionable recognized -> let the planner try other layers.
        return None

    def _is_iframe_shell(self, els) -> bool:
        """Detect if we're in a Workday iframe shell (empty top frame)."""
        # Check for Workday-specific iframe indicators
        workday_iframe_indicators = [
            "workday", "myworkdayjobs", "wd1.myworkday", "wd5.myworkday"
        ]
        for e in els:
            if e.tag == "iframe":
                src = (e.getAttribute("src") or "").lower()
                if any(indicator in src for indicator in workday_iframe_indicators):
                    return True
            # Also check for Workday shell in top frame
            t = text_of(e).lower()
            if "workday" in t and len(els) < 5:  # Very few elements = likely shell
                return True
        return False

    def _find_resume_upload(self, els) -> Optional[object]:
        """Find a file input for resume upload."""
        for e in els:
            if e.tag == "input" and e.type == "file":
                label = text_of(e)
                if any(w in label for w in ["resume", "cv", "upload", "attach", "parse"]):
                    return e
        return None

    def _is_account_wall(self, els) -> bool:
        # Wall = account CTA present AND no application form fields yet.
        has_form = any(e.tag in ("input", "textarea", "select") and
                       (e.type not in ("password", "email") or self._pw_context(els))
                       for e in els)
        wall_cta = find_button(els, ACCOUNT_WALL_WORDS) is not None
        only_auth = all(
            (e.type in ("password", "email", "text") or e.tag == "button")
            for e in els if e.tag in ("input", "button")
        )
        return wall_cta and only_auth and not self._has_application_fields(els)

    def _pw_context(self, els) -> bool:
        return any(e.type == "password" for e in els)

    def _has_application_fields(self, els) -> bool:
        # Application-y labels distinguish the real form from a login box.
        markers = ("experience", "education", "phone", "address", "resume",
                   "how did you hear", "work authorization", "years of experience",
                   "linkedin", "github", "portfolio", "cover letter", "salary",
                   "visa", "sponsorship", "citizenship", "relocate", "willing to travel")
        for e in els:
            t = text_of(e)
            if any(m in t for m in markers):
                return True
        return False

    def _handle_radio_questions(self, els, profile: Profile) -> Optional[list[Action]]:
        """Handle Workday's radio-button screening questions."""
        for e in els:
            if e.tag == "input" and e.type in ("radio", "checkbox"):
                if e.checked is False:
                    label = text_of(e)
                    val = profile.answer_for(label)
                    if val is not None:
                        val_lower = val.lower()
                        label_lower = label.lower()
                        # Match the radio value to the profile answer
                        if val_lower in ("yes", "true", "1", "y") and any(w in label_lower for w in ["yes", "true", "agree", "confirm", "authorized", "eligible"]):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        if val_lower in ("no", "false", "0", "n") and any(w in label_lower for w in ["no", "false", "disagree", "decline", "not authorized", "not eligible"]):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        # Handle "Authorized to work" type questions
                        if "authoriz" in label_lower and val_lower in ("yes", "true", "1"):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        if "sponsor" in label_lower and val_lower in ("no", "false", "0"):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        if "citizen" in label_lower and val_lower in ("yes", "true", "1"):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
                        if "relocat" in label_lower and val_lower in ("yes", "true", "1"):
                            return [Action(type=ActionType.CLICK, target_id=e.id)]
        return None

    def _handle_dropdowns(self, els, profile: Profile) -> Optional[list[Action]]:
        """Handle Workday's dropdown/select questions."""
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

    def _looks_done(self, els) -> bool:
        """Check if we're on the post-submit success screen."""
        done_markers = [
            "application sent", "your application was sent",
            "application submitted", "you applied",
            "application complete", "thanks for applying",
            "thank you for applying", "confirmation", "receipt",
            "your application has been received"
        ]
        for e in els:
            t = text_of(e)
            if any(marker in t for marker in done_markers):
                return True
        return False
