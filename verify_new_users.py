#!/usr/bin/env python3

import requests
import json

def test_login(email, password, expected_role):
    url = "http://localhost:8000/api/auth/login"
    data = {"email": email, "password": password}
    
    try:
        response = requests.post(url, json=data)
        print(f"🔐 Testing: {email}")
        
        if response.status_code == 200:
            result = response.json()
            user_role = result['user']['role']
            user_name = result['user']['name']
            
            if user_role == expected_role:
                print(f"✅ SUCCESS! {user_name} ({user_role})")
                return True
            else:
                print(f"⚠️  Login erfolgreich, aber falsche Rolle: {user_role} (erwartet: {expected_role})")
                return False
        else:
            print(f"❌ FAILED! Status: {response.status_code} | {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

print("🧪 TESTE NEUE ANMELDEDATEN")
print("=" * 50)

# Test alle drei neuen Accounts
test_accounts = [
    ("user@test.com", "password123", "user"),
    ("owner@test.com", "password123", "owner"), 
    ("admin@test.com", "password123", "admin")
]

successful_tests = 0
total_tests = len(test_accounts)

for email, password, expected_role in test_accounts:
    if test_login(email, password, expected_role):
        successful_tests += 1
    print("-" * 40)

print(f"\n🎯 TESTERGEBNIS: {successful_tests}/{total_tests} erfolgreich")

if successful_tests == total_tests:
    print("🎉 ALLE ANMELDEDATEN FUNKTIONIEREN!")
    print("\n📱 Sie können jetzt die App testen:")
    print("   🌐 http://localhost:3000")
    print("\n🔑 Verwenden Sie diese Anmeldedaten:")
    print("   👤 User: user@test.com / password123")
    print("   🏢 Owner: owner@test.com / password123") 
    print("   👑 Admin: admin@test.com / password123")
else:
    print("❌ Nicht alle Anmeldedaten funktionieren. Überprüfung erforderlich.")

print("\n✅ TEST ABGESCHLOSSEN")
