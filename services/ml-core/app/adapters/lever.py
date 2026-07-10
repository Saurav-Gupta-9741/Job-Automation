"""Lever ATS: a short, clean single-page form on jobs.lever.co.

Lever's apply button label is "Apply" / "Apply for this job"; the form itself is standard,
so we defer to the generic flow. Lever also has a "Resume/CV" dropzone that our upload
interceptor handles via the file-input path.
"""
from __future__ import annotations

from typing import Optional

from ..resume.profile import Profile
from ..schemas import Action, StepRequest
from .generic import GenericATSAdapter


class LeverAdapter(GenericATSAdapter):
    name = "lever"

    def matches(self, url: str) -> bool:
        return "lever.co" in url.lower()

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        return super().plan(req, profile)
