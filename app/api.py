from __future__ import annotations

import json
import mimetypes
import os
import base64
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .engine import FleetShieldEngine
from .faults import SUPPORTED_FAULTS
from .state_store import get_state_store


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
ENGINE = FleetShieldEngine()
STORE = get_state_store()


class FleetShieldHandler(BaseHTTPRequestHandler):
    server_version = "FleetShield/0.1"

    def log_message(self, format: str, *args: object) -> None:
        if os.getenv("FLEETSHIELD_QUIET") != "1":
            super().log_message(format, *args)

    def _json(self, payload: object, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, exc: Exception, status: int = HTTPStatus.BAD_REQUEST) -> None:
        self._json({"error": type(exc).__name__, "message": str(exc)}, status)

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length))

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"status": "ok", "service": "fleetshield", "version": "0.1.0"})
            return
        if path == "/api/state":
            self._json(ENGINE.snapshot())
            return
        if path == "/api/faults":
            self._json({"faults": SUPPORTED_FAULTS})
            return
        self._serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/reset":
                ENGINE.reset_runtime(keep_policies=bool(payload.get("keep_policies", False)))
                self._json(ENGINE.snapshot())
            elif path == "/api/run":
                fault = str(payload.get("fault", "timeout_after_commit"))
                if fault not in SUPPORTED_FAULTS:
                    raise ValueError(f"Unknown fault: {fault}")
                result = ENGINE.run(fault=fault)  # type: ignore[arg-type]
                STORE.save_snapshot(ENGINE.snapshot())
                self._json(result.to_dict())
            elif path == "/api/discover":
                policies = ENGINE.discover_from_last_failure()
                STORE.save_snapshot(ENGINE.snapshot())
                self._json({"policies": [asdict(policy) for policy in policies]})
            elif path == "/api/activate":
                policy_id = str(payload.get("policy_id", ""))
                policy = ENGINE.activate_policy(policy_id, str(payload.get("approved_by", "demo-reviewer")))
                STORE.save_snapshot(ENGINE.snapshot())
                self._json({"policy": asdict(policy)})
            elif path == "/api/demo":
                result = ENGINE.full_demo()
                STORE.save_snapshot(ENGINE.snapshot())
                self._json(result)
            elif path == "/api/events/pubsub":
                message = payload.get("message", {})
                if not isinstance(message, dict):
                    raise ValueError("Pub/Sub message must be an object")
                message_id = str(message.get("messageId") or message.get("message_id") or "")
                if not message_id:
                    raise ValueError("Pub/Sub messageId is required")
                encoded = str(message.get("data", ""))
                event = json.loads(base64.b64decode(encoded).decode()) if encoded else {}
                fault = str(event.get("fault", "timeout_after_commit"))
                if fault not in SUPPORTED_FAULTS:
                    raise ValueError(f"Unknown fault: {fault}")
                result = ENGINE.handle_event_once(message_id, fault)  # type: ignore[arg-type]
                STORE.save_snapshot(ENGINE.snapshot())
                self._json({"duplicate": result is None, "result": result.to_dict() if result else None})
            else:
                self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except KeyError as exc:
            self._error(exc, HTTPStatus.NOT_FOUND)
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self._error(exc)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            self._error(exc, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        candidate = (STATIC / relative).resolve()
        if STATIC.resolve() not in candidate.parents and candidate != STATIC.resolve():
            self._json({"error": "Invalid path"}, HTTPStatus.BAD_REQUEST)
            return
        if not candidate.is_file():
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve() -> None:
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), FleetShieldHandler)
    print(f"FleetShield listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
