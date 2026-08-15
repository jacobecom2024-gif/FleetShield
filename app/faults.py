from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Literal

from .models import ActionIntent

FaultName = Literal[
    "duplicate_event",
    "timeout_after_commit",
    "rate_limit_then_retry",
    "stale_evidence",
    "malformed_tool_result",
]


SUPPORTED_FAULTS: tuple[FaultName, ...] = (
    "duplicate_event",
    "timeout_after_commit",
    "rate_limit_then_retry",
    "stale_evidence",
    "malformed_tool_result",
)


def stale(intent: ActionIntent, seconds: int = 7200) -> ActionIntent:
    timestamp = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    return replace(intent, evidence_timestamp=timestamp.isoformat())

