# Getting Started

Phase 1 of Career OS is built and verified: backend planner + Chrome extension, wired
end-to-end with the human-in-the-loop handoff.

## 1. Run the backend

```bash
cd services/ml-core
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # then edit .env, add GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

Verify: open http://127.0.0.1:8000/health — you should see `{"ok": true, ...}`.
Dashboard: open http://127.0.0.1:8000/dashboard to watch every application live.

> The `.venv` is already created and deps installed in your workspace; just activate it.

## 2. Seed your profile (optional but recommended)

```bash
# put your resume path in .env  ->  RESUME_PDF_PATH=C:\path\to\resume.pdf
python -m app.seed_profile
```

Then open `services/ml-core/app/data/profile.json` and correct any blanks (salary,
work authorization, notice period). **This file is the agent's only source of truth —
it never invents facts about you.**

## 3. Load the extension

1. Chrome → `chrome://extensions` → enable **Developer mode**.
2. **Load unpacked** → select `apps/extension/`.
3. Open a LinkedIn job posting. The **Career OS** widget appears bottom-right.
4. Click **Apply on this page** and watch it work. When it hits something only you can
   do (CAPTCHA, OTP, a judgment question, or the final submit review), the widget pauses
   and asks you; solve it and tap **Resume**.

## 4. What works today (Phase 1)

- ✅ Deterministic-first planner (Router → Rules → Memory → LLM).
- ✅ LinkedIn Easy Apply state machine (open → fill → advance → review → submit).
- ✅ Named ATS adapters: Workday (account-wall handoff + autofill), Greenhouse, Lever, Cutshort (dropzone upload).
- ✅ Generic ATS adapter fallback for any other external redirect.
- ✅ Local dashboard at `/dashboard` (live application log + TPM usage).
- ✅ Human-in-the-loop handoff: CAPTCHA / OTP / OAuth / judgment / confirm-to-submit.
- ✅ Answer Bank (SQLite) — learns your answers so it stops asking over time.
- ✅ Token budgeter + circuit breaker for Groq's 6k TPM.
- ✅ Idempotent submit + application log + cross-session dedupe.
- ✅ Resume upload without the OS file picker (input injection + drag-drop fallback).
- ✅ Session survives reloads and external-redirect new tabs.
- ✅ Review-before-submit ON by default (`REVIEW_BEFORE_SUBMIT` in .env).

## 5. Test without a browser

```bash
cd services/ml-core
.venv\Scripts\python.exe -m tests.smoke
```

## 6. Next phases (see ARCHITECTURE.md §8)

- Phase 3: scanner v2 refinements + per-ATS quirks (Workday iframes, Cutshort dropzones).
- Phase 4: named adapters (Workday, Greenhouse, Lever, Cutshort) subclassing the generic one.
- Phase 5: local dashboard for the application log, dry-run mode toggle in the widget.

## Honest limits

- CAPTCHA / OTP / OAuth are **permanent manual touchpoints** — by design, no code removes them.
- This automates against sites' Terms of Service (LinkedIn especially). Human-like pacing
  is built in, but account risk is real. Use deliberately.
