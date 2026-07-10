"""Optional free push notifications via Telegram, for handoff pings.

If TELEGRAM_BOT_TOKEN/CHAT_ID aren't set, this is a silent no-op — the widget still shows
the handoff in-page. To enable: create a bot with @BotFather, get your chat id, put both
in .env.
"""
from __future__ import annotations

import httpx

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def push(message: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            )
    except Exception:
        pass  # notifications are best-effort, never block the agent
