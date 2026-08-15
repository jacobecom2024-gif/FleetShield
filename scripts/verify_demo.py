#!/usr/bin/env python3
"""Verify FleetShield's proof and, optionally, its live Google Cloud evidence."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def read_json(url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        url,
        data=body,
        headers={"content-type": "application/json"} if body else {},
        method="POST" if body else "GET",
    )
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8080")
    parser.add_argument("--require-cloud", action="store_true")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    try:
        health = read_json(f"{base}/api/health")
        demo = read_json(f"{base}/api/demo", {})
        evidence = read_json(f"{base}/api/evidence")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"FAIL: could not read FleetShield evidence: {exc}", file=sys.stderr)
        return 1

    checks = {
        "service healthy": health.get("status") == "ok",
        "vulnerable run duplicates": demo["vulnerable"]["actual_effects"] == 2,
        "protected replay has one effect": demo["protected"]["actual_effects"] == 1,
        "retry blocked before side effect": demo["protected"]["blocked_actions"] == 1,
        "protected replay is safe": demo["protected"]["safe"] is True,
    }
    if args.require_cloud:
        proof = evidence["qualifying_evidence"]
        checks.update(
            {
                "Google ADK + Gemini executed": proof["google_adk_executed"] is True,
                "Cloud Run active": proof["cloud_run_active"] is True,
            }
        )

    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
    print(json.dumps(evidence, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
