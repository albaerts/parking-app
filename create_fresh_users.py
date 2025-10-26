#!/usr/bin/env python3

import requests
import json

def create_user(name, email, password, role):
    url = "http://localhost:8000/api/auth/register"
    data = {
        "name": name,
        "email": email,
        "password": password,
        "role": role
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ User erstellt: {email} ({role})")
            return True
        else:
            print(f"❌ Fehler bei {email}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception bei {email}: {e}")
        return False

def test_login(email, password):
    url = "http://localhost:8000/api/auth/login"
    data = {"email": email, "password": password}
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login erfolgreich: {email} | {result['user']['name']} ({result['user']['role']})")
            return True
        else:
            print(f"❌ Login fehlgeschlagen: {email}")
            return False
    except Exception as e:
        print(f"❌ Login Fehler: {e}")
        return False

print("🚀 ERSTELLE NEUE, SAUBERE TEST-BENUTZER")
print("=" * 50)

# Neue, eindeutige Test-Benutzer erstellen
new_users = [
    ("Fresh User", "freshuser@test.com", "password123", "user"),
    ("Fresh Owner", "freshowner@test.com", "password123", "owner"), 
    ("Fresh Admin", "freshadmin@test.com", "password123", "admin")
]

created_users = []

for name, email, password, role in new_users:
    if create_user(name, email, password, role):
        created_users.append((email, password, role))

print(f"\n🎯 {len(created_users)} neue Benutzer erstellt!")

print("\n🔐 TESTE NEUE ANMELDEDATEN:")
print("=" * 50)

working_new_credentials = []

for email, password, role in created_users:
    if test_login(email, password):
        working_new_credentials.append((email, password, role))

print(f"\n🎉 NEUE FUNKTIONIERENDE ANMELDEDATEN:")
print("=" * 50)

for email, password, role in working_new_credentials:
    print(f"🎭 {role.upper()}: {email} / {password}")

print(f"\n📋 ALLE FUNKTIONIERENDEN OWNER-CREDENTIALS:")
print("=" * 50)
for email, password, role in working_new_credentials:
    if role == "owner":
        print(f"✅ {email} / {password} (neu erstellt)")
