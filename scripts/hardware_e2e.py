#!/usr/bin/env python3
"""End-to-end smoke test: assign device -> queue command -> poll -> ack

Usage: python3 scripts/hardware_e2e.py
"""
import requests
import time

BASE = "http://127.0.0.1:8000"
OWNER_TOKEN = "dev-token-owner"
HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}", "Content-Type": "application/json"}

hardware_id = "PARK_DEVICE_001"
spot_id = 1

print("1) Assign device to spot")
r = requests.post(f"{BASE}/api/owner/devices/assign", json={"hardware_id": hardware_id, "spot_id": spot_id}, headers=HEADERS)
print(r.status_code, r.text)

print("2) Queue raise_barrier command")
r = requests.post(f"{BASE}/api/hardware/{hardware_id}/commands/queue", json={"command":"raise_barrier","parameters":{"speed":"fast"}}, headers=HEADERS)
print(r.status_code, r.text)
resp = r.json()
cmd_id = resp.get('id')

print("3) Device polls for commands")
r = requests.get(f"{BASE}/api/hardware/{hardware_id}/commands")
print(r.status_code, r.text)

print("4) Ack command (if found)")
if cmd_id:
    r = requests.post(f"{BASE}/api/hardware/{hardware_id}/commands/{cmd_id}/ack", json={}, headers={"Content-Type": "application/json"})
    print(r.status_code, r.text)
else:
    print("No cmd_id returned to ack")

print("5) Poll again (should be empty)")
r = requests.get(f"{BASE}/api/hardware/{hardware_id}/commands")
print(r.status_code, r.text)

print("Done")
