#!/usr/bin/env python3
import requests, json

BASE = "http://localhost:8000/api/auth/login"
CANDIDATES = {
    "admin@test.com": ["admin123", "password123"],
    "owner@test.com": ["owner123", "password123"],
    "user@test.com":  ["user123", "password123"],
    "testuser@test.com": ["password123"],
    "user_3d029ec8@test.com": ["password123"],
    "freshuser@test.com": ["password123"],
    "freshowner@test.com": ["password123"],
    "freshadmin@test.com": ["password123"],
}

results = []
for email, pw_list in CANDIDATES.items():
    for pw in pw_list:
        try:
            r = requests.post(BASE, json={"email": email, "password": pw}, timeout=5)
            if r.status_code == 200:
                data = r.json()
                results.append({
                    "email": email,
                    "password": pw,
                    "role": data.get("user", {}).get("role"),
                    "name": data.get("user", {}).get("name"),
                })
                break
        except Exception:
            pass

print(json.dumps({"working": results}, ensure_ascii=False))
