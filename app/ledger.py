from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from .models import ActionIntent, LedgerEntry


class SandboxLedger:
    """A deliberately simple side-effect store used for reproducible demos."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def commit(self, intent: ActionIntent) -> LedgerEntry:
        entry = LedgerEntry(
            entry_id=str(uuid4()),
            action_id=intent.action_id,
            agent_id=intent.agent_id,
            tool_name=intent.tool_name,
            subject_id=intent.subject_id,
            amount=intent.amount,
            currency=intent.currency,
        )
        self._entries.append(entry)
        return entry

    def matching(self, tool_name: str, subject_id: str) -> list[LedgerEntry]:
        return [
            entry
            for entry in self._entries
            if entry.tool_name == tool_name and entry.subject_id == subject_id
        ]

    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def snapshot(self) -> list[dict[str, object]]:
        return [asdict(entry) for entry in self._entries]

    def reset(self) -> None:
        self._entries.clear()

