# Demo: Test the local Parking app logins

Use these curl examples to test the local demo logins and endpoints. Backend must be running at `http://127.0.0.1:8001`.

1) Login (demo accounts)

```bash
curl -X POST http://127.0.0.1:8001/login.php \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'
```

2) Register (demo, non-persistent)

```bash
curl -X POST http://127.0.0.1:8001/register.php \
  -H "Content-Type: application/json" \
  -d '{"name":"Dev","email":"dev@example.com","password":"devpass","role":"user"}'
```

3) Use token for requests

After login you'll get a token like `dev-token-admin`. Use it as:

```bash
curl -H "Authorization: Bearer dev-token-admin" http://127.0.0.1:8001/stats
```

4) Run the included automated script

```bash
python3 scripts/demo_tests.py
```

This writes `scripts/demo_report.json` with the test output.
