#!/usr/bin/env python3
"""
Test-Script für ESP32 Hardware-Verbindung

Dieses Script testet:
1. Ob das Backend läuft
2. Ob das Device in der DB registriert ist
3. Ob Commands gesendet werden können
4. Ob Telemetrie empfangen wird

Usage:
    python3 test_esp32_connection.py
"""

import requests
import json
import time
from datetime import datetime

# Konfiguration
BASE_URL = "http://localhost:8000"
DEVICE_ID = "PARK_DEVICE_001"

def test_backend():
    """Test 1: Backend erreichbar?"""
    print("\n" + "="*50)
    print("TEST 1: Backend-Verbindung")
    print("="*50)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Backend läuft auf {BASE_URL}")
        print(f"   Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        print(f"   Starte Backend mit: uvicorn backend.server_gashis:app --reload --port 8000")
        return False

def test_device_registration():
    """Test 2: Device in DB?"""
    print("\n" + "="*50)
    print("TEST 2: Device-Registrierung")
    print("="*50)
    
    try:
        # Hole alle Devices (Admin-Endpoint)
        response = requests.get(
            f"{BASE_URL}/api/owner/devices",
            headers={"Authorization": "Bearer dev-token-admin"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            devices = data.get('devices', [])
            
            # Suche unser Device
            our_device = None
            for d in devices:
                if d.get('hardware_id') == DEVICE_ID:
                    our_device = d
                    break
            
            if our_device:
                print(f"✅ Device gefunden: {DEVICE_ID}")
                print(f"   Owner: {our_device.get('owner_email', 'N/A')}")
                print(f"   Spot: {our_device.get('parking_spot_id', 'N/A')}")
                print(f"   Registriert: {our_device.get('created_at', 'N/A')}")
                
                if our_device.get('last_heartbeat'):
                    print(f"   Letzter Heartbeat: {our_device.get('last_heartbeat')}")
                    print(f"   Batterie: {our_device.get('battery_level', 'N/A')} V")
                    print(f"   RSSI: {our_device.get('rssi', 'N/A')} dBm")
                    print(f"   Belegung: {our_device.get('occupancy', 'N/A')}")
                else:
                    print(f"   ⚠️  Noch keine Telemetrie empfangen")
                
                return True
            else:
                print(f"⚠️  Device {DEVICE_ID} nicht in DB gefunden")
                print(f"   Verfügbare Devices: {[d.get('hardware_id') for d in devices]}")
                print(f"   Weise Device in der Web-App zu!")
                return False
        else:
            print(f"❌ Fehler beim Abrufen: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_send_command():
    """Test 3: Command senden"""
    print("\n" + "="*50)
    print("TEST 3: Command senden")
    print("="*50)
    
    try:
        # Sende test command
        payload = {
            "command": "raise_barrier",
            "parameters": {}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/hardware/{DEVICE_ID}/commands/queue",
            headers={
                "Authorization": "Bearer dev-token-owner",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Command erfolgreich gesendet")
            print(f"   Command-ID: {data.get('id')}")
            print(f"   Command: {data.get('command')}")
            print(f"   Status: {data.get('status')}")
            print(f"\n   ESP32 wird Command beim nächsten Poll abholen (max. 10s)")
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_poll_commands():
    """Test 4: Commands abholen (simuliert ESP32)"""
    print("\n" + "="*50)
    print("TEST 4: Commands abholen (ESP32-Simulation)")
    print("="*50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/hardware/{DEVICE_ID}/commands",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            commands = data.get('commands', [])
            
            if commands:
                print(f"✅ {len(commands)} Command(s) in Queue:")
                for cmd in commands:
                    print(f"   → ID: {cmd.get('id')}, Command: {cmd.get('command')}")
            else:
                print(f"✅ Keine Commands in Queue")
            
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_send_telemetry():
    """Test 5: Telemetrie senden (simuliert ESP32)"""
    print("\n" + "="*50)
    print("TEST 5: Telemetrie senden (ESP32-Simulation)")
    print("="*50)
    
    try:
        payload = {
            "battery_level": 3.7,
            "rssi": -55,
            "occupancy": "free",
            "timestamp": datetime.now().isoformat(),
            "last_mag": {
                "x": 0.1,
                "y": 0.2,
                "z": 0.9
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/hardware/{DEVICE_ID}/telemetry",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Telemetrie erfolgreich gesendet")
            print(f"   Hardware-ID: {data.get('hardware_id')}")
            print(f"   Heartbeat: {data.get('last_heartbeat')}")
            print(f"\n   Überprüfe im Geräte-Tab der Web-App!")
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def main():
    print("\n" + "="*50)
    print("ESP32 Hardware-Verbindung Tester")
    print("="*50)
    print(f"Device-ID: {DEVICE_ID}")
    print(f"Backend: {BASE_URL}")
    
    # Test-Sequenz
    results = []
    
    # Test 1: Backend
    results.append(("Backend", test_backend()))
    if not results[-1][1]:
        print("\n❌ Backend nicht erreichbar. Weitere Tests übersprungen.")
        return
    
    time.sleep(1)
    
    # Test 2: Device Registration
    results.append(("Device-Registrierung", test_device_registration()))
    
    time.sleep(1)
    
    # Test 3: Send Command
    results.append(("Command senden", test_send_command()))
    
    time.sleep(1)
    
    # Test 4: Poll Commands
    results.append(("Commands abholen", test_poll_commands()))
    
    time.sleep(1)
    
    # Test 5: Send Telemetry
    results.append(("Telemetrie senden", test_send_telemetry()))
    
    # Zusammenfassung
    print("\n" + "="*50)
    print("ZUSAMMENFASSUNG")
    print("="*50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n{passed}/{total} Tests bestanden")
    
    if passed == total:
        print("\n🎉 Alle Tests erfolgreich!")
        print("\nNächste Schritte:")
        print("1. Öffne http://localhost:3000")
        print("2. Login als albert@gashis.ch")
        print("3. Gehe zu Tab '📡 Geräte'")
        print("4. Lade ESP32-Sketch auf dein Board")
        print("5. Öffne Serial Monitor (115200 baud)")
    else:
        print("\n⚠️  Einige Tests fehlgeschlagen")
        print("\nÜberprüfe:")
        print("- Backend läuft: uvicorn backend.server_gashis:app --reload --port 8000")
        print("- Device zugewiesen in Web-App")
        print("- Firewall erlaubt Port 8000")

if __name__ == "__main__":
    main()
