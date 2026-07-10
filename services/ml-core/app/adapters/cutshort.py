"""Cutshort ATS: custom-built forms on cutshort.io with non-standard dropzones.

Cutshort's resume upload is a custom dropzone (no plain <input type=file> visible), which
is exactly the case our upload interceptor's drag-and-drop fallback was built for. We add
Cutshort's fingerprint and its "Apply"/"Submit" vocabulary and otherwise defer to generic.
"""
from __future__ import annotations

from typing import Optional

from ..resume.profile import Profile
from ..schemas import Action, ActionType, StepRequest
from .generic import GenericATSAdapter, UPLOAD_WORDS
from .base import find_button


class CutshortAdapter(GenericATSAdapter):
    name = "cutshort"

    def matches(self, url: str) -> bool:
        return "cutshort.io" in url.lower()

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        els = req.elements
        # Cutshort dropzone: an element labeled drag/drop resume -> force upload path so the
        # interceptor's synthetic drop events fire (there's no native file input to set).
        drop = find_button(els, ["drag", "drop your resume", "drop resume"] + UPLOAD_WORDS)
        if drop and self._needs_resume(els):
            return [Action(type=ActionType.UPLOAD_RESUME, target_id=drop.id)]
        return super().plan(req, profile)

    def _needs_resume(self, els) -> bool:
        for e in els:
            if e.type == "file" and e.value:
                return False
        return True
