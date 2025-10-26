#!/usr/bin/env python3
"""
Test-Script für gashis.ch Parking App
Testet alle Endpoints nach dem Deployment
"""

import requests
import json

BASE_URL = "https://gashis.ch/parking"
API_URL = f"{BASE_URL}/api"

def test_frontend():
    """Test ob Frontend erreichbar ist"""
    print("🧪 Testing Frontend...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend erreichbar: https://gashis.ch/parking")
            return True
        else:
            print(f"❌ Frontend Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend nicht erreichbar: {e}")
        return False

def test_api_health():
    """Test API Health Check"""
    print("\n🔍 Testing API Health...")
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API erreichbar: https://gashis.ch/parking/api")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API nicht erreichbar: {e}")
        return False

def test_parking_spots():
    """Test Parkplätze Endpoint"""
    print("\n🚗 Testing Parking Spots...")
    try:
        response = requests.get(f"{API_URL}/parking-spots", timeout=10)
        if response.status_code == 200:
            spots = response.json()
            print(f"✅ Parkplätze geladen: {len(spots)} Schweizer Spots")
            
            # Zeige erste 3 Spots
            for i, spot in enumerate(spots[:3]):
                status_emoji = "🟢" if spot['status'] == 'free' else "🔴"
                print(f"   {status_emoji} {spot['name']}: {spot['status']} (CHF {spot['price_per_hour']}/h)")
            
            if len(spots) > 3:
                print(f"   ... und {len(spots)-3} weitere")
            
            return True
        else:
            print(f"❌ Parkplätze Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Parkplätze nicht verfügbar: {e}")
        return False

def test_api_docs():
    """Test API Dokumentation"""
    print("\n📚 Testing API Documentation...")
    try:
        response = requests.get(f"{API_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API Dokumentation: https://gashis.ch/parking/api/docs")
            return True
        else:
            print(f"❌ API Docs Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Docs nicht erreichbar: {e}")
        return False

def test_stats():
    """Test Statistiken Endpoint"""
    print("\n📊 Testing Statistics...")
    try:
        response = requests.get(f"{API_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistiken verfügbar:")
            print(f"   Total: {stats.get('total', 0)} Parkplätze")
            print(f"   Frei: {stats.get('free', 0)}")
            print(f"   Besetzt: {stats.get('occupied', 0)}")
            print(f"   Reserviert: {stats.get('reserved', 0)}")
            return True
        else:
            print(f"❌ Stats Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats nicht verfügbar: {e}")
        return False

def main():
    """Hauptfunktion - führt alle Tests aus"""
    print("🚀 Gashis.ch Parking App - Deployment Test")
    print("=" * 50)
    
    tests = [
        test_frontend,
        test_api_health,
        test_parking_spots,
        test_stats,
        test_api_docs
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🏆 Test Ergebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests erfolgreich! Deine App läuft perfekt auf gashis.ch")
        print("\n📱 Teile diese URLs mit deinen Freunden:")
        print(f"   App: {BASE_URL}")
        print(f"   API: {API_URL}/docs")
    else:
        print("⚠️  Einige Tests fehlgeschlagen. Prüfe das Deployment.")
    
    return passed == total

if __name__ == "__main__":
    main()
