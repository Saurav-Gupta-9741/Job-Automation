"""Offline smoke test of the planner pipeline (no server, no LLM needed).

Run from services/ml-core:
    .venv\\Scripts\\python.exe -m tests.smoke
"""
from __future__ import annotations

from app.schemas import Element, StepRequest
from app.planner.pipeline import plan_step
from app.resume.profile import save_profile


def _req(url, elements, **kw):
    return StepRequest(session_id="smoke-1", url=url, elements=elements,
                       total_elements=len(elements), stage_hash=kw.pop("stage", "s1"),
                       **kw)


def main() -> None:
    # Give the profile some facts so deterministic fills fire.
    save_profile({
        "first_name": "Asha", "last_name": "Rao", "full_name": "Asha Rao",
        "email": "asha@example.com", "phone": "+91 90000 00000",
        "years_experience": "5", "work_authorization": "Authorized to work in India",
        "requires_sponsorship": "No", "skills": ["Python", "FastAPI"],
    })

    print("\n[1] LinkedIn job page, not in modal -> should click Easy Apply")
    els = [Element(id="b1", tag="button", text="Easy Apply")]
    r = plan_step(_req("https://www.linkedin.com/jobs/view/123", els, stage="s0"))
    print("   ", r.source, [a.type for a in r.script])

    print("\n[2] In modal with an empty phone field -> should fill_all from profile")
    els = [
        Element(id="i1", tag="input", type="tel", text="Mobile phone number",
                required=True, value=""),
        Element(id="nb", tag="button", text="Next"),
    ]
    r = plan_step(_req("https://www.linkedin.com/jobs/view/123", els, stage="s1"))
    print("   ", r.source, [(a.type, a.fields) for a in r.script])

    print("\n[3] All filled, Review button -> review-before-submit handoff")
    els = [Element(id="rb", tag="button", text="Submit application")]
    r = plan_step(_req("https://www.linkedin.com/jobs/view/123", els, stage="s2"))
    print("   ", r.source, [(a.type, a.input_kind, a.prompt) for a in r.script])

    print("\n[4] CAPTCHA present -> safety handoff")
    els = [Element(id="c1", tag="div", text="Please verify you are human (reCAPTCHA)")]
    r = plan_step(_req("https://boards.greenhouse.io/acme/jobs/1", els, stage="s3"))
    print("   ", r.source, [(a.type, a.input_kind) for a in r.script])

    print("\n[5] Unknown field the profile can't answer -> ask_user")
    els = [Element(id="q1", tag="input", type="text",
                   text="What is your favorite programming paradigm?",
                   required=True, value="")]
    r = plan_step(_req("https://jobs.lever.co/acme/1", els, stage="s4"))
    print("   ", r.source, [(a.type, a.prompt) for a in r.script])

    print("\n[6] Router picks the right adapter per URL")
    from app.planner.router import route
    cases = {
        "https://www.linkedin.com/jobs/view/1": "linkedin",
        "https://acme.wd1.myworkdayjobs.com/en-US/careers/job/1": "workday",
        "https://boards.greenhouse.io/acme/jobs/1": "greenhouse",
        "https://jobs.lever.co/acme/1": "lever",
        "https://cutshort.io/job/1": "cutshort",
        "https://careers.randomco.com/apply/1": "generic",
    }
    for url, expected in cases.items():
        got = route(url).name
        flag = "OK" if got == expected else "MISMATCH"
        print(f"    {flag:8} {expected:11} <- {url.split('//')[1][:40]}")

    print("\n[7] Workday account wall -> handoff")
    els = [
        Element(id="w1", tag="input", type="email", text="Email"),
        Element(id="w2", tag="input", type="password", text="Password"),
        Element(id="w3", tag="button", text="Sign In to apply"),
    ]
    r = plan_step(_req("https://acme.wd1.myworkdayjobs.com/careers/job/1", els, stage="s6"))
    print("   ", r.source, [(a.type, a.prompt) for a in r.script])

    print("\n[8] Greenhouse form fills known fields")
    els = [
        Element(id="g1", tag="input", type="email", text="Email", value=""),
        Element(id="g2", tag="input", type="text", text="First Name", value=""),
        Element(id="gs", tag="button", text="Submit Application"),
    ]
    r = plan_step(_req("https://boards.greenhouse.io/acme/jobs/1", els, stage="s7"))
    print("   ", r.source, [(a.type, getattr(a, "fields", None)) for a in r.script])

    print("\nSmoke test complete.")


if __name__ == "__main__":
    main()
