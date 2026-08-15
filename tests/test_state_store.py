import tempfile
import unittest
from pathlib import Path

from app.state_store import FileStateStore


class FileStateStoreTests(unittest.TestCase):
    def test_message_claim_is_idempotent_and_releasable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = FileStateStore(str(Path(directory) / "state.json"))
            self.assertTrue(store.claim_message("message-1"))
            self.assertFalse(store.claim_message("message-1"))
            store.release_message("message-1")
            self.assertTrue(store.claim_message("message-1"))


if __name__ == "__main__":
    unittest.main()
