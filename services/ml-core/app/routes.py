"""HTTP surface. One planning endpoint + resume asset + small profile helpers."""
from __future__ import annotations

import base64

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from .config import RESUME_ASSET_PATH

_STATIC_DIR = Path(__file__).resolve().parent / "static"
from .planner.pipeline import plan_step
from .resume.profile import load_profile, save_profile
from .schemas import ActionType, StepRequest, StepResponse
from . import notify, storage
from .telemetry import get_stats

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    html = (_STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@router.post("/api/agent/step", response_model=StepResponse)
def agent_step(req: StepRequest) -> StepResponse:
    resp = plan_step(req)
    # Fire a handoff notification when we ask the user for help.
    if any(a.type == ActionType.ASK_USER for a in resp.script):
        prompt = next((a.prompt for a in resp.script
                       if a.type == ActionType.ASK_USER and a.prompt), "Need your help")
        notify.push(f"Career OS: {prompt}\n{req.title or req.url}")
    return resp


@router.get("/api/resume")
def get_resume() -> JSONResponse:
    """Return the resume as base64 so the extension can inject it into file inputs."""
    if not RESUME_ASSET_PATH.exists():
        raise HTTPException(404, "No resume staged. Run seed_profile with RESUME_PDF_PATH.")
    data = base64.b64encode(RESUME_ASSET_PATH.read_bytes()).decode()
    return JSONResponse({"filename": "resume.pdf", "mime": "application/pdf",
                         "base64": data})


@router.get("/api/profile")
def get_profile() -> dict:
    return load_profile().data


@router.put("/api/profile")
def put_profile(data: dict) -> dict:
    save_profile(data)
    return {"ok": True}



@router.get("/api/applications")
def list_applications() -> list[dict]:
    with storage._lock:  # noqa: SLF001 - simple read for the local dashboard
        rows = storage._conn.execute(
            "SELECT session_id, url, company, title, status, submitted, updated_at "
            "FROM applications ORDER BY updated_at DESC LIMIT 200"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/export/csv")
def export_applications_csv() -> str:
    """Export all applications to CSV format."""
    import csv
    from io import StringIO
    
    with storage._lock:
        rows = storage._conn.execute(
            """
            SELECT session_id, url, company, title, status, submitted, 
                   created_at, updated_at 
            FROM applications 
            ORDER BY created_at DESC
            """
        ).fetchall()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Session ID', 'URL', 'Company', 'Title', 'Status', 
                     'Submitted', 'Created At', 'Updated At'])
    
    # Write data
    for row in rows:
        writer.writerow([
            row['session_id'], row['url'], row['company'], row['title'],
            row['status'], 'Yes' if row['submitted'] else 'No',
            row['created_at'], row['updated_at']
        ])
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=career_os_applications.csv'}
    )


@router.get("/api/usage")
def get_usage() -> dict:
    """Get current month's usage and quota."""
    return storage.get_usage()


@router.post("/api/license")
def activate_license(payload: dict) -> dict:
    """Activate a license key to upgrade to Pro tier."""
    key = payload.get("key", "").strip()
    if not key or len(key) < 8:
        raise HTTPException(400, "Invalid license key")
    if not key.startswith("COS-"):
        raise HTTPException(400, "Invalid key format. Keys start with COS-")
    result = storage.activate_license(key, tier="pro", limit=50)
    return {"ok": True, "usage": result}


@router.get("/api/config")
def get_config() -> dict:
    """Get current LLM provider config (key masked)."""
    from .llm.client import get_user_config, has_api_key
    cfg = get_user_config()
    cfg["has_key"] = has_api_key()
    return cfg


@router.put("/api/config")
def put_config(payload: dict) -> dict:
    """Update LLM provider config (BYOK)."""
    from .llm.client import set_user_config
    set_user_config(
        provider=payload.get("provider", "groq"),
        api_key=payload.get("api_key", ""),
        model=payload.get("model", ""),
    )
    return {"ok": True}


@router.get("/api/stats")
def get_telemetry_stats(days: int = 7) -> dict:
    """
    Get aggregate telemetry statistics for the last N days.
    
    Returns metrics including:
    - Completion rate
    - Error statistics  
    - Loop incidents
    - LLM efficiency (memory hits vs LLM calls)
    - Handoff frequency
    """
    try:
        return get_stats(days)
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve stats: {str(e)}")
