from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol


class StateStore(Protocol):
    backend: str

    def save_snapshot(self, snapshot: dict[str, Any]) -> None: ...

    def claim_message(self, message_id: str) -> bool: ...

    def release_message(self, message_id: str) -> None: ...


class FileStateStore:
    backend = "file"

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("FLEETSHIELD_STATE_FILE", "/tmp/fleetshield-state.json"))
        self.claimed_messages: set[str] = set()

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
        temporary.replace(self.path)

    def claim_message(self, message_id: str) -> bool:
        if message_id in self.claimed_messages:
            return False
        self.claimed_messages.add(message_id)
        return True

    def release_message(self, message_id: str) -> None:
        self.claimed_messages.discard(message_id)


class FirestoreStateStore:
    backend = "firestore"

    def __init__(self) -> None:
        from google.cloud import firestore  # type: ignore[import-not-found]

        self.firestore = firestore
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

    def claim_message(self, message_id: str) -> bool:
        """Atomically claim a Pub/Sub delivery before running the experiment."""

        reference = self.client.collection("ingress_messages").document(message_id)
        transaction = self.client.transaction()

        @self.firestore.transactional
        def claim(current_transaction: Any) -> bool:
            if reference.get(transaction=current_transaction).exists:
                return False
            current_transaction.create(
                reference,
                {
                    "message_id": message_id,
                    "claimed_at": self.firestore.SERVER_TIMESTAMP,
                },
            )
            return True

        return bool(claim(transaction))

    def release_message(self, message_id: str) -> None:
        self.client.collection("ingress_messages").document(message_id).delete()


def get_state_store() -> StateStore:
    requested = os.getenv("FLEETSHIELD_STATE_BACKEND", "file")
    if requested == "firestore":
        return FirestoreStateStore()
    return FileStateStore()
