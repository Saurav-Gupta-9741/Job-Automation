"""Workday ATS: a multi-page wizard on *.myworkdayjobs.com.

Workday is the hard one, with three quirks the generic flow doesn't know about:

  1. Account wall — most Workday tenants force "Create Account / Sign In" before applying.
     Credentials are the user's, so we hand off (ask_user) rather than guess.
  2. Multi-page wizard — advances via "Save and Continue" / "Next", one section per page.
     Our generic NEXT_WORDS already covers these; we add Workday's exact phrasing.
  3. Iframes — some tenants render the form in an iframe. The content script currently
     scans the top frame only; if we detect an empty top frame with a Workday shell, we
     ask the user to interact so we don't silently stall. (Full iframe support = Phase 5.)
"""
from __future__ import annotations

from typing import Optional

from ..resume.profile import Profile
from ..schemas import Action, ActionType, StepRequest
from .generic import GenericATSAdapter
from .base import find_button, text_of

ACCOUNT_WALL_WORDS = ["create account", "sign in to apply", "create an account",
                      "sign in", "verify new password", "register"]
AUTOFILL_WORDS = ["autofill with resume", "use my last application",
                  "autofill from resume"]


class WorkdayAdapter(GenericATSAdapter):
    name = "workday"

    def matches(self, url: str) -> bool:
        u = url.lower()
        return "myworkdayjobs.com" in u or "workday" in u or "wd1.myworkday" in u

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        els = req.elements

        # 1) Prefer Workday's own "Autofill with Resume" — fastest, most accurate path.
        autofill = find_button(els, AUTOFILL_WORDS)
        if autofill:
            return [Action(type=ActionType.CLICK, target_id=autofill.id)]

        # 2) Account wall -> hand off (user's own credentials / verification email).
        if self._is_account_wall(els):
            return [Action(
                type=ActionType.ASK_USER, input_kind="manual",
                prompt="Workday needs you to create an account / sign in. Do that, then tap Resume.",
            )]

        # 3) Otherwise the standard multi-page flow (generic handles Save and Continue).
        return super().plan(req, profile)

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
                   "how did you hear", "work authorization")
        for e in els:
            t = text_of(e)
            if any(m in t for m in markers):
                return True
        return False
