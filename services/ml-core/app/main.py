"""FastAPI entry point."""
from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS
from .routes import router
from .storage import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('career_os.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Career OS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def _startup() -> None:
    logger.info("Career OS backend starting up...")
    init_db()
    logger.info("Database initialized successfully")
    logger.info(f"Backend ready at http://127.0.0.1:8000")


@app.get("/health")
def health() -> dict:
    from .llm.budgeter import breaker, budgeter
    return {
        "ok": True,
        "tokens_spent_60s": budgeter.spent(),
        "tpm_budget": budgeter.budget,
        "circuit_open": breaker.is_open,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
