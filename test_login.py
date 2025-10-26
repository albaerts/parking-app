#!/usr/bin/env python3

import requests
import json

# Test Login Function
def test_login(email, password):
    url = "http://localhost:8000/api/auth/login"
    data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"🔐 Testing login: {email}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! User: {result['user']['name']} | Role: {result['user']['role']}")
            return True
        else:
            print(f"❌ FAILED! Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    print("-" * 50)

# Test verschiedene Owner-Credentials
print("🧪 TESTING OWNER CREDENTIALS")
print("=" * 50)

owner_credentials = [
    ("owner@test.com", "password123"),
    ("owner@example.com", "password123"),
    ("info@binzstudio.ch", "password123"),
    ("testowner@example.com", "password123"),
    ("owner@owner.com", "password123")
]

successful_logins = []

for email, password in owner_credentials:
    if test_login(email, password):
        successful_logins.append((email, password))
    print("-" * 50)

print("\n🎯 FUNKTIONIERENDE OWNER-CREDENTIALS:")
print("=" * 50)
for email, password in successful_logins:
    print(f"✅ Email: {email} | Password: {password}")

if not successful_logins:
    print("❌ Keine funktionierenden Owner-Credentials gefunden!")

print("\n🔍 Zusätzlich funktionierende User/Admin Credentials:")
print("=" * 50)

# Test auch andere Credentials
other_credentials = [
    ("user@test.com", "password123"),
    ("admin@test.com", "password123"),
    ("test@example.com", "password123"),
    ("admin@example.com", "password123")
]

for email, password in other_credentials:
    if test_login(email, password):
        pass
    print("-" * 30)
