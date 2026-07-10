"""Prompt construction for the LLM fallback.

The LLM is only ever asked a *narrow* question: given a small set of unresolved fields and
a slice of the user's profile, return values (or say it can't). Strict JSON, no prose.
"""
from __future__ import annotations

import json
from ..schemas import Element

SYSTEM = (
    "You are a form-filling assistant for a single user's job applications. "
    "You are given the user's profile facts and a few unresolved form fields. "
    "For each field, return the correct value taken ONLY from the profile. "
    "NEVER invent facts (experience, employers, salary, personal data). "
    "If a field needs a value not present in the profile, or requires human judgment "
    "(essays, 'why do you want this job'), set its value to null and needs_user to true. "
    "Respond with STRICT JSON only, no markdown, matching exactly:\n"
    '{"answers":[{"id":"<element id>","value":<string|null>,'
    '"needs_user":<bool>,"confidence":<0..1>}]}'
)


def build_user_prompt(profile_slice: str, elements: list[Element]) -> str:
    fields = [
        {
            "id": e.id,
            "label": (e.text or e.placeholder or e.name or "")[:80],
            "type": e.type or e.tag,
            "options": e.options[:12] if e.options else [],
            "required": e.required,
        }
        for e in elements
    ]
    return (
        "USER PROFILE:\n"
        f"{profile_slice}\n\n"
        "UNRESOLVED FIELDS:\n"
        f"{json.dumps(fields, ensure_ascii=False)}\n\n"
        "Return the JSON now."
    )
