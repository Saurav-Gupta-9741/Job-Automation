"""Adapter interface + shared deterministic helpers used by every platform adapter.

An adapter encodes what we know about a platform's flow. Given the perceived step it
returns a list of Actions to run, or `None` to defer to the next planner layer (memory/LLM).
The helpers here (find buttons, fill known profile fields) are the zero-token workhorses.
"""
from __future__ import annotations

import re
from typing import Optional

from ..resume.profile import Profile
from ..schemas import Action, ActionType, Element, StepRequest


class Adapter:
    name: str = "base"

    def matches(self, url: str) -> bool:  # pragma: no cover - overridden
        return False

    def plan(self, req: StepRequest, profile: Profile) -> Optional[list[Action]]:
        raise NotImplementedError


# --- element helpers -----------------------------------------------------------

def text_of(e: Element) -> str:
    return " ".join(filter(None, [e.text, e.name, e.placeholder, e.value])).lower()


def find_button(elements: list[Element], phrases: list[str],
                require_enabled: bool = True) -> Optional[Element]:
    for e in elements:
        if e.tag not in ("button", "a") and e.type not in ("button", "submit"):
            if e.type != "button":
                continue
        if require_enabled and e.disabled:
            continue
        t = text_of(e)
        if any(p in t for p in phrases):
            return e
    return None


def is_fillable(e: Element) -> bool:
    if e.disabled:
        return False
    if e.tag == "textarea":
        return True
    if e.tag == "select":
        return True
    if e.tag == "input":
        return (e.type or "text") in (
            "text", "email", "tel", "number", "url", "search", None
        )
    return False


def empty(e: Element) -> bool:
    return not (e.value and e.value.strip())


# Common submit/advance vocab.
NEXT_WORDS = ["next", "continue", "review", "save and continue"]
SUBMIT_WORDS = ["submit application", "submit", "apply now", "send application"]


def fill_known_fields(elements: list[Element], profile: Profile) -> list[Action]:
    """Fill every empty field we can answer deterministically from the profile.
    Fills both required AND optional fields if the profile has the data."""
    fields = []
    for e in elements:
        if not is_fillable(e) or not empty(e):
            continue
        val = profile.answer_for(e.text or e.placeholder or e.name or "")
        if val is None:
            continue
        if e.tag == "select":
            fields.append({"target_id": e.id, "value": val, "select": True})
        else:
            fields.append({"target_id": e.id, "value": val})
    if not fields:
        return []
    return [Action(type=ActionType.FILL_ALL, fields=fields)]


def unresolved_fields(elements: list[Element], profile: Profile,
                      required_only: bool = False) -> list[Element]:
    """Fillable, empty fields we could NOT answer from the profile.

    If required_only=True, returns ONLY required (star-marked) fields.
    This prevents optional empty fields from blocking form submission.
    """
    out = []
    for e in elements:
        if not is_fillable(e) or not empty(e):
            continue
        if required_only and not e.required:
            continue  # Skip optional fields — don't block progress
        if profile.answer_for(e.text or e.placeholder or e.name or "") is None:
            out.append(e)
    return out
