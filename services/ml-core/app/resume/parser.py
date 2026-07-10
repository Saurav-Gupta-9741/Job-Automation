"""Parse a resume PDF into raw text and a best-effort structured profile.

Field extraction here is intentionally light (regex heuristics). It gets you a usable
profile.json immediately; you then hand-correct it once and it stays your source of truth.
"""
from __future__ import annotations

import re
import shutil
from typing import Any

from pypdf import PdfReader

from ..config import RESUME_ASSET_PATH

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s]+", re.I)
_GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s]+", re.I)
_YEARS = re.compile(r"(\d+)\+?\s*(?:years|yrs)", re.I)


def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def parse_resume(pdf_path: str) -> dict[str, Any]:
    text = extract_text(pdf_path)
    profile: dict[str, Any] = {"raw_text": text}

    if m := _EMAIL.search(text):
        profile["email"] = m.group(0)
    if m := _PHONE.search(text):
        profile["phone"] = re.sub(r"\s+", " ", m.group(0)).strip()
    if m := _LINKEDIN.search(text):
        profile["linkedin"] = m.group(0)
    if m := _GITHUB.search(text):
        profile["github"] = m.group(0)
    if m := _YEARS.search(text):
        profile["years_experience"] = m.group(1)

    # Name heuristic: first non-empty line, if it isn't contact info.
    for line in text.splitlines():
        line = line.strip()
        if line and "@" not in line and not _PHONE.search(line) and len(line) < 50:
            parts = line.split()
            if 1 <= len(parts) <= 4 and all(p[:1].isalpha() for p in parts):
                profile["full_name"] = line
                profile["first_name"] = parts[0]
                profile["last_name"] = parts[-1] if len(parts) > 1 else ""
                break

    profile["summary"] = text[:600].strip()
    return profile


def stage_resume_asset(pdf_path: str) -> None:
    """Copy the resume next to the app so the extension can fetch it for uploads."""
    shutil.copyfile(pdf_path, RESUME_ASSET_PATH)
