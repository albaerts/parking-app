#!/usr/bin/env python3
import os
import sys
import time
import requests

BASE = os.environ.get("BASE", "https://parking.gashis.ch/api").rstrip("/")

results = []

def log_info(name, msg=""):
    # Neutral info line that doesn't count as pass/fail in the summary
    print(f"ℹ️  {name} - {msg}")

def log(name, ok, msg=""):
    results.append((name, ok, msg))
    symbol = "✅" if ok else "❌"
    print(f"{symbol} {name} - {msg}")

# 0. Health
try:
    r = requests.get(f"{BASE}/health", timeout=10)
    ok = (r.status_code == 200 and r.json().get("status") == "ok")
    log("GET /health", ok, f"status={r.status_code}")
except Exception as e:
    log("GET /health", False, str(e))

# 1. Parking spots
try:
    r = requests.get(f"{BASE}/parking-spots", timeout=10)
    ok = (r.status_code == 200 and isinstance(r.json(), list))
    log("GET /parking-spots", ok, f"status={r.status_code}")
except Exception as e:
    log("GET /parking-spots", False, str(e))

# 2. Geo search
try:
    r = requests.get(f"{BASE}/geo/search", params={"q": "Migros", "limit": 3}, timeout=15)
    ok = (r.status_code == 200 and isinstance(r.json(), list))
    log("GET /geo/search", ok, f"status={r.status_code} len={len(r.json()) if ok else 'n/a'}")
except Exception as e:
    log("GET /geo/search", False, str(e))

# 3. Autocomplete (API root)
try:
    r = requests.get(f"{BASE}/autocomplete", params={"q": "B", "limit": 5, "lat": 47.3769, "lon": 8.5417}, timeout=10)
    ok = (r.status_code == 200 and isinstance(r.json(), list))
    log("GET /autocomplete", ok, f"status={r.status_code} len={len(r.json()) if ok else 'n/a'}")
except Exception as e:
    log("GET /autocomplete", False, str(e))

# 4. Rate limit smoke (optional, informational)
if os.environ.get("DISABLE_RATE_LIMIT_PROBE", "0") not in ("1", "true", "True"):
    violations = 0
    for i in range(4):
        try:
            rq = requests.get(f"{BASE}/autocomplete", params={"q": f"Rate{i}", "limit": 1}, timeout=8)
            if rq.status_code == 429:
                violations += 1
                break
        except Exception:
            pass
    log_info("Rate limit probe", f"violations_detected={violations}")
else:
    log_info("Rate limit probe", "skipped via DISABLE_RATE_LIMIT_PROBE=1")

print("\nSummary:")
passed = sum(1 for _, ok, _ in results if ok)
print(f"{passed}/{len(results)} checks passed")
# Require at least health and parking-spots OK
mandatory = {
    "GET /health": False,
    "GET /parking-spots": False,
}
for name, ok, _ in results:
    if name in mandatory:
        mandatory[name] = ok

if all(mandatory.values()):
    sys.exit(0)
else:
    sys.exit(1)
