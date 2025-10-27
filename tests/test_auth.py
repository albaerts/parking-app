import os
import uuid
import requests

BASE = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")


def test_register_login_flow():
    email = f"smoke+{uuid.uuid4().hex[:8]}@example.com"
    name = "smoke_user"
    password = "TestPass123!"

    # Register
    r = requests.post(f"{BASE}/register.php", data={"name": name, "email": email, "password": password})
    assert r.status_code in (200, 201), f"register status {r.status_code} body={r.text}"
    j = r.json()
    assert "token" in j, f"no token returned: {j}"

    # Login
    r2 = requests.post(f"{BASE}/login.php", data={"email": email, "password": password})
    assert r2.status_code == 200, f"login status {r2.status_code} body={r2.text}"
    j2 = r2.json()
    assert "token" in j2
