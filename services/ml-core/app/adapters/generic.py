"""Generic ATS adapter: a sane default form flow for external redirect pages.

Used for Greenhouse / Lever / unknown ATS. It fills known fields, defers unknowns to the
memory/LLM layer, handles resume upload, and advances/submits with the review gate. Named
ATS adapters can later subclass this and override quirks (Workday iframes, etc.).
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
    find_button,
    fill_known_fields,
    text_of,
    unresolved_fields,
)

UPLOAD_WORDS = ["upload resume", "attach resume", "upload cv", "attach cv",
                "upload", "attach", "choose file", "add resume"]
APPLY_WORDS = ["apply for this job", "apply now", "apply", "i'm interested"]


class GenericATSAdapter(Adapter):
    name = "generic"

    def matches(self, url: str) -> bool:
        return True  # last-resort adapter; router places it last

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        els = req.elements

        # Landing page with an Apply button but no form yet -> open the form.
        if not _has_form(els):
            apply = find_button(els, APPLY_WORDS)
            if apply:
                return [Action(type=ActionType.CLICK, target_id=apply.id)]

        # Ensure resume is attached if an upload control is present and no file field set.
        upload = find_button(els, UPLOAD_WORDS)
        if upload and _needs_resume(els):
            return [Action(type=ActionType.UPLOAD_RESUME, target_id=upload.id)]

        # Fill everything we know.
        fills = fill_known_fields(els, profile)
        if fills:
            return fills

        # Unknown fields remain -> memory/LLM layer.
        if unresolved_fields(els, profile):
            return None

        # Advance or submit.
        submit = find_button(els, SUBMIT_WORDS)
        if submit:
            if REVIEW_BEFORE_SUBMIT:
                return [Action(
                    type=ActionType.ASK_USER,
                    input_kind="confirm",
                    prompt="Review this application, then confirm to submit.",
                    target_id=submit.id,
                )]
            return [Action(type=ActionType.CLICK, target_id=submit.id)]

        nxt = find_button(els, NEXT_WORDS)
        if nxt:
            return [Action(type=ActionType.CLICK, target_id=nxt.id)]

        return None


def _has_form(els: list[Element]) -> bool:
    return any(e.tag in ("input", "textarea", "select") for e in els)


def _needs_resume(els: list[Element]) -> bool:
    # If there's a file input already holding a value, assume attached.
    for e in els:
        if e.type == "file" and e.value:
            return False
    return True
