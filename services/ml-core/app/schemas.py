"""The contract between the extension and the planner.

The extension PERCEIVEs the page and posts a `StepRequest`. The planner THINKs and
returns a `StepResponse` whose `script` the extension then ACTs on.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"           # choose an option in a native/custom dropdown
    FILL_ALL = "fill_all"       # batch-fill several fields in one script
    UPLOAD_RESUME = "upload_resume"
    ASK_USER = "ask_user"       # hand the wheel to the human, then resume
    SCROLL_DOWN = "scroll_down"
    WAIT = "wait"
    DONE = "done"               # application submitted / flow complete
    ABORT = "abort"             # unrecoverable; stop cleanly


class Element(BaseModel):
    """One interactive element as seen by the scanner."""
    id: str                                 # stable-ish id assigned by the scanner
    tag: str
    type: Optional[str] = None              # input type, role, etc.
    text: str = ""                          # visible/label text (truncated by scanner)
    name: Optional[str] = None
    placeholder: Optional[str] = None
    value: Optional[str] = None
    required: bool = False
    disabled: bool = False
    checked: Optional[bool] = None
    options: list[str] = Field(default_factory=list)  # for selects
    signature: str = ""                     # stable fingerprint for re-location


class StepRequest(BaseModel):
    session_id: str
    url: str
    title: str = ""
    # Only the elements that changed since the last step (diffed client-side).
    elements: list[Element] = Field(default_factory=list)
    # Full element count on the page (for the planner to reason about completeness).
    total_elements: int = 0
    # A short, stable hash of the visible stage (for anti-loop detection).
    stage_hash: str = ""
    # What the user answered during the last ask_user handoff, if anything.
    user_input: Optional[dict[str, Any]] = None
    # Free-form objective, e.g. "apply to this job".
    objective: str = "apply"
    # Security tokens extracted from the page (CSRF, session tokens)
    security_tokens: Optional[dict[str, Any]] = None
    # Optional base64 screenshot of the page for Vision LLM fallback
    screenshot: Optional[str] = None


class Action(BaseModel):
    type: ActionType
    target_id: Optional[str] = None
    value: Optional[str] = None
    # For fill_all: list of {target_id, value}.
    fields: list[dict[str, Any]] = Field(default_factory=list)
    # For ask_user: what we need and how to collect it.
    prompt: Optional[str] = None
    input_kind: Optional[Literal["text", "otp", "file", "confirm", "manual"]] = None
    # Milliseconds, for wait.
    ms: Optional[int] = None


class StepResponse(BaseModel):
    session_id: str
    script: list[Action]
    # Where the decision came from — invaluable for debugging and trust.
    source: Literal["rule", "memory", "llm", "safety"] = "rule"
    stage: str = ""             # human-readable current stage
    reason: str = ""            # one-line explanation
    tokens_used: int = 0
