from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol


class StateStore(Protocol):
    backend: str

    def save_snapshot(self, snapshot: dict[str, Any]) -> None: ...


class FileStateStore:
    backend = "file"

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("FLEETSHIELD_STATE_FILE", "/tmp/fleetshield-state.json"))

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
        temporary.replace(self.path)


class FirestoreStateStore:
    backend = "firestore"

    def __init__(self) -> None:
        from google.cloud import firestore  # type: ignore[import-not-found]

        self.client = firestore.Client()

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        # The latest control-plane view is useful for the demo. Individual runs and
        # policies are also written separately so evidence remains queryable.
        batch = self.client.batch()
        batch.set(self.client.collection("system").document("fleetshield"), snapshot)
        for policy in snapshot.get("policies", []):
            batch.set(self.client.collection("policies").document(policy["policy_id"]), policy)
        last = snapshot.get("last_result")
        if last:
            batch.set(self.client.collection("experiments").document(last["run_id"]), last)
        batch.commit()


def get_state_store() -> StateStore:
    requested = os.getenv("FLEETSHIELD_STATE_BACKEND", "file")
    if requested == "firestore":
        return FirestoreStateStore()
    return FileStateStore()
