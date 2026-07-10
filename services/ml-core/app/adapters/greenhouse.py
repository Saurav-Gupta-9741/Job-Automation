"""Greenhouse ATS: a single long application form on boards.greenhouse.io.

The generic flow already handles it well (fill known -> resolve unknown -> submit). We add
the precise URL fingerprint and Greenhouse's exact submit/apply vocabulary so buttons are
matched deterministically.
"""
from __future__ import annotations

from typing import Optional

from ..resume.profile import Profile
from ..schemas import Action, StepRequest
from .generic import GenericATSAdapter, APPLY_WORDS
from .base import find_button


class GreenhouseAdapter(GenericATSAdapter):
    name = "greenhouse"

    def matches(self, url: str) -> bool:
        u = url.lower()
        return "greenhouse.io" in u or "boards.greenhouse" in u or "grnh.se" in u

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        # Greenhouse embeds a "Apply for this job" reveal on some boards; generic handles it.
        return super().plan(req, profile)
