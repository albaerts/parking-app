#!/usr/bin/env python3
import requests
import sqlite3
import os
import time
import uuid

BASE = os.environ.get("BASE", "http://127.0.0.1:8000")
DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'parking.db')

results = []

def log(name, ok, msg=""):
    results.append((name, ok, msg))
    print(("✅" if ok else "❌"), name, "-", msg)

# 1. Probe parking-spots
try:
    r = requests.get(f"{BASE}/parking-spots", timeout=10)
    ok = (r.status_code == 200 and isinstance(r.json(), list))
    log("GET /parking-spots", ok, f"status={r.status_code}")
except Exception as e:
    log("GET /parking-spots", False, str(e))

# 2. Register owner via legacy endpoint
email = f"owner_{uuid.uuid4().hex[:8]}@example.com"
pwd = "password123"
try:
    payload = {"name":"Smoke Owner","email":email,"password":pwd,"role":"owner"}
    r = requests.post(f"{BASE}/register.php", json=payload, timeout=15)
    ok = (r.status_code == 200)
    log("POST /register.php", ok, f"status={r.status_code}")
except Exception as e:
    log("POST /register.php", False, str(e))

# 3. Fetch verification token from sqlite and verify
verified = False
token = None
if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT verification_token FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        if row and row[0]:
            token = row[0]
        conn.close()
    except Exception as e:
        log("Read token from DB", False, str(e))
else:
    log("Read token from DB", False, f"db not found: {DB_PATH}")

if token:
    try:
        r = requests.get(f"{BASE}/verify-email/{token}", allow_redirects=False, timeout=10)
        ok = (r.status_code in (200, 307, 302))
        verified = ok
        log("GET /verify-email/{token}", ok, f"status={r.status_code}")
    except Exception as e:
        log("GET /verify-email/{token}", False, str(e))
else:
    log("GET /verify-email/{token}", False, "no token")

# 4. Login via legacy endpoint
jwt_token = None
try:
    r = requests.post(f"{BASE}/login.php", json={"email":email,"password":pwd}, timeout=15)
    ok = (r.status_code == 200 and r.json().get("token"))
    if ok:
        jwt_token = r.json().get("token")
    log("POST /login.php", ok, f"status={r.status_code}")
except Exception as e:
    log("POST /login.php", False, str(e))

# 5. Create parking spot (unauthenticated in this backend)
try:
    payload = {
        "name": "Smoke Spot",
        "address": "Bahnhofplatz 1, 8001 Zürich",
        "latitude": 47.3783,
        "longitude": 8.5398,
        "status": "free",
        "price_per_hour": 2.5
    }
    r = requests.post(f"{BASE}/parking-spots", json=payload, timeout=15)
    ok = (r.status_code == 200 and r.json().get("id") is not None)
    log("POST /parking-spots", ok, f"status={r.status_code}")
except Exception as e:
    log("POST /parking-spots", False, str(e))

# 6. Geo search
try:
    r = requests.get(f"{BASE}/geo/search", params={"q":"Migros","limit":3}, timeout=15)
    ok = (r.status_code == 200 and isinstance(r.json(), list))
    log("GET /geo/search", ok, f"status={r.status_code} len={len(r.json()) if ok else 'n/a'}")
except Exception as e:
    log("GET /geo/search", False, str(e))

# 7. Autocomplete (new unified endpoint) basic coverage
try:
    r = requests.get(f"{BASE}/api/autocomplete", params={"q": "B", "limit": 5, "lat":47.3769, "lon":8.5417}, timeout=15)
    data = r.json() if r.status_code == 200 else []
    ok = (r.status_code == 200 and isinstance(data, list))
    log("GET /api/autocomplete (B)", ok, f"status={r.status_code} len={len(data) if ok else 'n/a'}")
except Exception as e:
    log("GET /api/autocomplete (B)", False, str(e))

# 8. Autocomplete caching check (second identical request should be fast)
try:
    t0 = time.time()
    r2 = requests.get(f"{BASE}/api/autocomplete", params={"q": "B", "limit": 5, "lat":47.3769, "lon":8.5417}, timeout=15)
    dt = (time.time() - t0) * 1000
    ok = (r2.status_code == 200)
    log("GET /api/autocomplete cache hit", ok, f"{dt:.1f}ms")
except Exception as e:
    log("GET /api/autocomplete cache hit", False, str(e))

# 9. Autocomplete rate limit probe (fire > 3 quick requests)
violations = 0
for i in range(4):
    try:
        rq = requests.get(f"{BASE}/api/autocomplete", params={"q": f"Rate{i}", "limit": 1}, timeout=10)
        if rq.status_code == 429:
            violations += 1
            break
    except Exception:
        pass
log("Rate limit engaged?", violations > 0, f"violations_detected={violations}")

print("\nSummary:")
passed = sum(1 for _,ok,_ in results if ok)
print(f"{passed}/{len(results)} checks passed")
exit(0 if passed == len(results) else 1)

