"""The canonical profile: the single source of truth about the user.

The LLM never invents facts about the user; it only *selects/formats* values from here.
`answer_for()` maps a form field/label to a value using synonym matching — this is what
lets the deterministic rule engine fill common fields at zero token cost.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from ..config import PROFILE_PATH
from ..storage import normalize_question

# A sensible default so the app runs before you seed a real resume.
DEFAULT_PROFILE: dict[str, Any] = {
    "first_name": "",
    "last_name": "",
    "full_name": "",
    "email": "",
    "phone": "",
    "location": "",
    "city": "",
    "country": "",
    "linkedin": "",
    "website": "",
    "github": "",
    "current_company": "",
    "current_title": "",
    "years_experience": "",
    "desired_salary": "",
    "notice_period": "",
    "work_authorization": "",       # e.g. "Authorized to work in India"
    "requires_sponsorship": "No",
    "willing_to_relocate": "Yes",
    "gender": "",
    "ethnicity": "",
    "veteran_status": "",
    "disability_status": "",
    "residential_address": "",
    "summary": "",
    "skills": [],
    "raw_text": "",                 # full resume text, for LLM context slices
}

# label synonyms -> profile key. Order matters (more specific first).
_FIELD_SYNONYMS: list[tuple[list[str], str]] = [
    (["first name", "given name", "fname"], "first_name"),
    (["last name", "surname", "family name", "lname"], "last_name"),
    (["full name", "your name", "name"], "full_name"),
    (["email", "e-mail"], "email"),
    (["phone", "mobile", "contact number", "telephone"], "phone"),
    (["linkedin"], "linkedin"),
    (["github"], "github"),
    (["portfolio", "website", "personal site"], "website"),
    (["current company", "employer"], "current_company"),
    (["current title", "current role", "job title", "designation"], "current_title"),
    (["years of experience", "total experience", "years experience",
      "how many years"], "years_experience"),
    (["desired salary", "expected salary", "salary expectation",
      "compensation"], "desired_salary"),
    (["notice period"], "notice_period"),
    (["work authorization", "authorized to work", "right to work",
      "legally authorized"], "work_authorization"),
    (["require sponsorship", "need sponsorship", "visa sponsorship"],
     "requires_sponsorship"),
    (["relocate", "relocation", "willing to move"], "willing_to_relocate"),
    (["residential address", "street address", "address", "mailing address",
      "home address"], "residential_address"),
    (["city"], "city"),
    (["country"], "country"),
    (["location", "current location", "where are you"], "location"),
    (["gender"], "gender"),
    (["ethnicity", "race"], "ethnicity"),
    (["veteran"], "veteran_status"),
    (["disability"], "disability_status"),
]


class Profile:
    def __init__(self, data: dict[str, Any]):
        self.data = {**DEFAULT_PROFILE, **data}
        # Derive full_name if missing.
        if not self.data.get("full_name"):
            self.data["full_name"] = (
                f"{self.data.get('first_name','')} {self.data.get('last_name','')}"
            ).strip()

    def get(self, key: str, default: Any = "") -> Any:
        return self.data.get(key, default)

    def answer_for(self, label: str) -> Optional[str]:
        """Deterministically map a field label to a profile value, or None."""
        norm = normalize_question(label)
        if not norm:
            return None
        for synonyms, key in _FIELD_SYNONYMS:
            if any(s in norm for s in synonyms):
                val = self.data.get(key)
                if isinstance(val, str) and key in ('skills',):
                    val = [s.strip() for s in val.split(',') if s.strip()]
                if isinstance(val, list):
                    val = ", ".join(val)
                if val not in (None, ""):
                    return str(val)
        return None

    def context_slice(self, max_chars: int = 2500) -> str:
        """A compact profile summary for LLM prompts."""
        d = self.data
        raw_lines = [
            f"Name: {d.get('full_name')}",
            f"Email: {d.get('email')}  Phone: {d.get('phone')}",
            f"Location: {d.get('location')}  City: {d.get('city')}",
            f"Current role: {d.get('current_title')} at {d.get('current_company')}",
            f"Experience: {d.get('years_experience')} years",
            f"Education: {d.get('education', '')} | Degree: {d.get('degree', '')}",
            f"Skills: {', '.join(d.get('skills', [])[:25])}",
            f"Desired salary: {d.get('desired_salary', 'Negotiable')}",
            f"Notice period: {d.get('notice_period', 'Immediately available')}",
            f"Work auth: {d.get('work_authorization')}  "
            f"Sponsorship needed: {d.get('requires_sponsorship')}  "
            f"Relocate: {d.get('willing_to_relocate')}",
            f"Gender: {d.get('gender', '')}  Veteran: {d.get('veteran_status', '')}",
            f"Summary: {d.get('summary', '')[:500]}",
            f"Resume: {d.get('raw_text', '')[:300]}",
        ]
        # Skip empty fields (lines where all values after the label are blank)
        lines = []
        for line in raw_lines:
            # Extract everything after the first colon
            parts = line.split(":", 1)
            if len(parts) == 2:
                value_part = parts[1].strip()
                # Skip if the value portion is empty or contains only separators/whitespace
                cleaned = value_part.replace("|", "").replace("at", "").strip()
                if not cleaned or cleaned in ("years", "Negotiable", "Immediately available"):
                    continue
            lines.append(line)
        return "\n".join(lines)[:max_chars]


def load_profile() -> Profile:
    if PROFILE_PATH.exists():
        try:
            return Profile(json.loads(PROFILE_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return Profile(DEFAULT_PROFILE)


def save_profile(data: dict[str, Any]) -> None:
    merged = {**DEFAULT_PROFILE, **data}
    PROFILE_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
