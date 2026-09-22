"""Shared demo state: an event log fed by every page."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import reflex as rx


def _short(value: Any, limit: int = 110) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[: limit - 1] + "…"


class DemoState(rx.State):
    """Base state; page states inherit from it to share the event log."""

    events: list[dict[str, str]] = []
    show_log: bool = True

    def _log(self, kind: str, detail: Any = "") -> None:
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "kind": kind,
            "detail": _short(detail),
        }
        self.events = [entry, *self.events][:8]

    @rx.event
    def clear_log(self):
        self.events = []

    @rx.event
    def toggle_log(self):
        self.show_log = not self.show_log
