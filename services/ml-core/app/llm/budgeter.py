"""Rolling tokens-per-minute budgeter + circuit breaker for Groq's free tier.

The budgeter tracks token spend over a sliding 60s window and tells callers how long to
wait before a request of a given size would fit under the TPM cap — so we queue instead of
getting 429'd. The circuit breaker trips after N consecutive failures so the planner falls
back to a safe ask_user action instead of crash-looping.
"""
from __future__ import annotations

import threading
import time
from collections import deque

from ..config import GROQ_TPM_BUDGET, LLM_FAILURE_THRESHOLD


class TokenBudgeter:
    def __init__(self, tpm_budget: int = GROQ_TPM_BUDGET, window_s: int = 60):
        self.budget = tpm_budget
        self.window = window_s
        self._events: deque[tuple[float, int]] = deque()  # (timestamp, tokens)
        self._lock = threading.Lock()

    def _prune(self, now: float) -> None:
        while self._events and now - self._events[0][0] > self.window:
            self._events.popleft()

    def _spent(self, now: float) -> int:
        self._prune(now)
        return sum(t for _, t in self._events)

    def seconds_until_fits(self, needed: int, now: float | None = None) -> float:
        """How long to sleep before `needed` tokens fit under the window budget."""
        now = now if now is not None else time.monotonic()
        with self._lock:
            self._prune(now)
            if self._spent(now) + needed <= self.budget:
                return 0.0
            # Wait until enough old events age out of the window.
            running = self._spent(now)
            for ts, tok in list(self._events):
                running -= tok
                if running + needed <= self.budget:
                    return max(0.0, self.window - (now - ts))
            return float(self.window)

    def record(self, tokens: int, now: float | None = None) -> None:
        now = now if now is not None else time.monotonic()
        with self._lock:
            self._events.append((now, tokens))
            self._prune(now)

    def spent(self) -> int:
        return self._spent(time.monotonic())


class CircuitBreaker:
    def __init__(self, threshold: int = LLM_FAILURE_THRESHOLD):
        self.threshold = threshold
        self._failures = 0
        self._lock = threading.Lock()

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._failures >= self.threshold

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1


# Shared singletons.
budgeter = TokenBudgeter()
breaker = CircuitBreaker()
