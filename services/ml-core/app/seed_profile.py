"""Parse your resume PDF into profile.json and stage it for uploads.

Usage (from services/ml-core, with your venv active):
    set RESUME_PDF_PATH=C:\\path\\to\\resume.pdf   # or put it in .env
    python -m app.seed_profile

Then open data/profile.json and hand-correct anything the parser missed. That file is
your permanent source of truth — the agent never invents facts outside it.
"""
from __future__ import annotations

import sys

from .config import RESUME_PDF_PATH
from .resume.parser import parse_resume, stage_resume_asset
from .resume.profile import load_profile, save_profile


def main() -> int:
    pdf = RESUME_PDF_PATH or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not pdf:
        print("Set RESUME_PDF_PATH in .env or pass a path: python -m app.seed_profile <pdf>")
        return 1
    print(f"Parsing {pdf} ...")
    parsed = parse_resume(pdf)
    existing = load_profile().data
    merged = {**existing, **{k: v for k, v in parsed.items() if v}}
    save_profile(merged)
    stage_resume_asset(pdf)
    print("Wrote data/profile.json and staged data/resume.pdf.")
    print("Review data/profile.json and fill in any blank fields (salary, work auth, etc.).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
