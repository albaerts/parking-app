#!/usr/bin/env python3
"""
Demo test runner for the local Parking app.

What it does:
- POST to /login.php for demo accounts (user/owner/admin)
- POST to /register.php with a test email (route is non-persistent)
- GET /stats using the admin token
- GET /parking-spots
- Write a JSON report to scripts/demo_report.json and print a short summary

No data is modified in the SQLite DB by these calls (register is a demo route that returns a token).
"""
import json
import sys
from urllib import request, error

BASE = "http://127.0.0.1:8001"
REPORT_PATH = "scripts/demo_report.json"

def post_json(path, payload):
    url = BASE + path
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except error.HTTPError as e:
        return {"error": True, "status": e.code, "msg": e.read().decode(errors="ignore")}
    except Exception as e:
        return {"error": True, "msg": str(e)}

def get_json(path, token=None):
    url = BASE + path
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except error.HTTPError as e:
        return {"error": True, "status": e.code, "msg": e.read().decode(errors="ignore")}
    except Exception as e:
        return {"error": True, "msg": str(e)}

def main():
    report = {"logins": {}, "register": None, "stats": None, "parking_spots_count": None}

    demo_accounts = [
        ("user@test.com", "user123"),
        ("owner@test.com", "owner123"),
        ("admin@test.com", "admin123"),
    ]

    # Login each demo account
    for email, pwd in demo_accounts:
        res = post_json("/login.php", {"email": email, "password": pwd})
        report["logins"][email] = res

    # Register test (non-persistent route)
    reg_payload = {"name": "Scripted Dev", "email": "scripted-dev@example.com", "password": "devpass", "role": "user"}
    report["register"] = post_json("/register.php", reg_payload)

    # Use admin token if available (from demo logins)
    admin_token = None
    admin_login = report["logins"].get("admin@test.com")
    if admin_login and isinstance(admin_login, dict) and admin_login.get("token"):
        admin_token = admin_login.get("token")

    report["stats"] = get_json("/stats", token=admin_token)

    parks = get_json("/parking-spots")
    if isinstance(parks, list):
        report["parking_spots_count"] = len(parks)
        report["parking_spots_sample"] = parks[:5]
    else:
        report["parking_spots_count"] = None
        report["parking_spots_sample"] = parks

    # Save report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("Demo tests finished. Report written to:", REPORT_PATH)
    print(json.dumps({
        "logins": {k: (v.get("user")["role"] if isinstance(v, dict) and v.get("user") else "err") for k,v in report["logins"].items()},
        "parking_spots_count": report["parking_spots_count"],
        "stats": report["stats"] if isinstance(report["stats"], dict) else {"error": True}
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(1)
