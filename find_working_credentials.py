#!/usr/bin/env python3

import requests
import json

def test_login(email, password):
    url = "http://localhost:8000/api/auth/login"
    data = {"email": email, "password": password}
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "name": result['user']['name'],
                "role": result['user']['role'],
                "email": email,
                "password": password
            }
        else:
            return {"success": False, "email": email}
    except Exception as e:
        return {"success": False, "email": email, "error": str(e)}

# Alle bekannten E-Mail-Adressen aus der Datenbank
all_emails = [
    "user@test.com",
    "owner@test.com",
    "admin@test.com",
    "testuser@test.com",
    "user_3d029ec8@test.com",
    "freshuser@test.com",
    "freshowner@test.com",
    "freshadmin@test.com",
]

print("🔍 ALLE FUNKTIONIERENDEN ANMELDEDATEN:")
print("=" * 60)

working_credentials = {
    "user": [],
    "owner": [],
    "admin": []
}

for email in all_emails:
    result = test_login(email, "password123")
    if result["success"]:
        role = result["role"]
        working_credentials[role].append(result)
        print(f"✅ {role.upper()}: {email} / password123 | Name: {result['name']}")

print("\n" + "=" * 60)
print("📋 ZUSAMMENFASSUNG - FUNKTIONIERENDE ANMELDEDATEN:")
print("=" * 60)

for role, users in working_credentials.items():
    if users:
        print(f"\n🎭 {role.upper()} ACCOUNTS:")
        for user in users:
            print(f"   📧 {user['email']} / {user['password']}")
            print(f"   👤 {user['name']}")
            print(f"   ---")

if not working_credentials["owner"]:
    print("\n❌ KEINE FUNKTIONIERENDEN OWNER-ACCOUNTS GEFUNDEN!")
else:
    print(f"\n🎉 {len(working_credentials['owner'])} funktionierende Owner-Accounts gefunden!")
