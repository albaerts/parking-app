#!/usr/bin/env python3
"""
Simple production API smoke test.

Checks:
- GET {BASE}/parking-spots (expects 200 JSON list)
- GET {BASE}/stats (expects 200 JSON dict)
- GET https://parking.gashis.ch/hardware/PARK_DEVICE_001/telemetry (expects 200 JSON dict)

Usage:
  BASE=https://parking.gashis.ch/api python3 scripts/smoke_api_only.py

Exit codes:
  0 = all checks passed
  1 = one or more checks failed
"""
import json
import os
import sys
from urllib import request, error

BASE = os.environ.get("BASE", "https://parking.gashis.ch/api").rstrip("/")
HARDWARE_URL = "https://parking.gashis.ch/hardware/PARK_DEVICE_001/telemetry"


def get_json(url):
    req = request.Request(url, headers={"Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=10) as r:
            ctype = r.headers.get("Content-Type", "")
            data = r.read()
            try:
                payload = json.loads(data.decode("utf-8"))
            except Exception:
                payload = {"parse_error": data[:200].decode("utf-8", errors="ignore")}
            return r.status, ctype, payload
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return e.code, e.headers.get("Content-Type", ""), {"error": True, "body": body[:300]}
    except Exception as e:
        return 0, "", {"error": True, "msg": str(e)}


def main():
    failures = []

    # 1) parking-spots
    status, ctype, payload = get_json(f"{BASE}/parking-spots")
    ok = status == 200 and isinstance(payload, list)
    print("[parking-spots]", status, "OK" if ok else "FAIL", "count=", (len(payload) if isinstance(payload, list) else None))
    if not ok:
        failures.append(("parking-spots", status, payload))

    # 2) stats
    status, ctype, payload = get_json(f"{BASE}/stats")
    ok = status == 200 and isinstance(payload, dict) and all(k in payload for k in ("total", "free", "occupied"))
    print("[stats]", status, "OK" if ok else "FAIL", payload if not ok else payload)
    if not ok:
        failures.append(("stats", status, payload))

    # 3) hardware device telemetry direct (no /api)
    status, ctype, payload = get_json(HARDWARE_URL)
    ok = status == 200 and isinstance(payload, dict) and "hardware_id" in payload
    print("[hardware telemetry]", status, "OK" if ok else "FAIL", payload if not ok else {k: payload.get(k) for k in ("hardware_id", "parking_spot_id", "telemetry")})
    if not ok:
        failures.append(("hardware-telemetry", status, payload))

    if failures:
        print("\nOne or more smoke checks failed:")
        for name, st, pl in failures:
            print(f" - {name}: status={st}, details={str(pl)[:300]}")
        sys.exit(1)

    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(1)
