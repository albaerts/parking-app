#!/usr/bin/env python3
"""
Smart Parking Barrier - Test & Debug Script
Dieses Script testet alle Hardware-Komponenten einzeln
"""

import RPi.GPIO as GPIO
import time
import requests
import subprocess
import sys

# GPIO Pin Configuration (gleich wie main script)
SERVO_PIN = 18
LED_GREEN = 23
LED_RED = 24
LED_BLUE = 25

# Servo Positionen
SERVO_DOWN = 2.5
SERVO_UP = 12.5

def setup_gpio():
    """GPIO Setup"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_BLUE, GPIO.OUT)
    
    # LEDs ausschalten
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(LED_BLUE, GPIO.LOW)

def test_leds():
    """LED Test"""
    print("🔥 LED Test wird gestartet...")
    
    leds = [
        (LED_GREEN, "Grün"),
        (LED_RED, "Rot"), 
        (LED_BLUE, "Blau")
    ]
    
    for pin, color in leds:
        print(f"  💡 {color} LED an...")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(pin, GPIO.LOW)
        print(f"  💡 {color} LED aus")
        time.sleep(0.5)
    
    print("✅ LED Test abgeschlossen\n")

def test_servo():
    """Servo Test"""
    print("🦾 Servo Test wird gestartet...")
    
    try:
        servo = GPIO.PWM(SERVO_PIN, 50)
        servo.start(0)
        
        # Test-Sequenz
        positions = [
            (SERVO_DOWN, "DOWN (horizontal/frei)"),
            (SERVO_UP, "UP (vertikal/blockiert)"),
            (SERVO_DOWN, "DOWN (zurück zu frei)")
        ]
        
        for position, description in positions:
            print(f"  🔄 Servo → {description}")
            servo.ChangeDutyCycle(position)
            time.sleep(2)
            servo.ChangeDutyCycle(0)  # PWM stoppen
            time.sleep(1)
        
        servo.stop()
        print("✅ Servo Test abgeschlossen\n")
        
    except Exception as e:
        print(f"❌ Servo Fehler: {e}\n")

def test_internet():
    """Internet-Verbindung testen"""
    print("🌐 Internet-Verbindung wird getestet...")
    
    try:
        # Ping Test
        result = subprocess.run(
            ['ping', '-c', '3', '8.8.8.8'], 
            capture_output=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Internet-Verbindung OK")
            
            # HTTP Test
            try:
                response = requests.get('https://httpbin.org/ip', timeout=5)
                if response.status_code == 200:
                    ip_info = response.json()
                    print(f"  📍 Externe IP: {ip_info.get('origin', 'Unbekannt')}")
                else:
                    print("⚠️ HTTP Test fehlgeschlagen")
            except:
                print("⚠️ HTTP Test Fehler")
        else:
            print("❌ Keine Internet-Verbindung")
            
    except Exception as e:
        print(f"❌ Internet Test Fehler: {e}")
    
    print()

def test_4g_stick():
    """4G USB-Stick testen"""
    print("📱 4G USB-Stick wird getestet...")
    
    try:
        # USB-Geräte auflisten
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        
        if 'Huawei' in result.stdout:
            print("✅ Huawei USB-Stick erkannt")
            
            # Netzwerk-Interfaces prüfen
            net_result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            
            interfaces = []
            for line in net_result.stdout.split('\n'):
                if 'wwan' in line or 'ppp' in line:
                    interfaces.append(line.strip())
            
            if interfaces:
                print("✅ 4G Netzwerk-Interface gefunden:")
                for interface in interfaces:
                    print(f"  📡 {interface}")
            else:
                print("⚠️ Kein 4G Interface aktiv")
                
        else:
            print("❌ Huawei USB-Stick nicht gefunden")
            print("  💡 Überprüfe USB-Verbindung")
            
    except Exception as e:
        print(f"❌ 4G Test Fehler: {e}")
    
    print()

def test_system_info():
    """System-Informationen anzeigen"""
    print("🖥️ System-Informationen:")
    
    try:
        # CPU Temperatur
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
            print(f"  🌡️ CPU Temperatur: {temp:.1f}°C")
        
        # Memory Info
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            
        mem_total = int([l for l in lines if 'MemTotal' in l][0].split()[1]) // 1024
        mem_free = int([l for l in lines if 'MemFree' in l][0].split()[1]) // 1024
        mem_used = mem_total - mem_free
        
        print(f"  💾 RAM: {mem_used}MB / {mem_total}MB ({(mem_used/mem_total)*100:.1f}%)")
        
        # Disk Space
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        disk_line = result.stdout.split('\n')[1]
        disk_parts = disk_line.split()
        
        print(f"  💽 Disk: {disk_parts[2]} / {disk_parts[1]} ({disk_parts[4]})")
        
        # Uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            uptime_minutes = uptime_seconds // 60
            
        print(f"  ⏰ Uptime: {uptime_minutes:.0f} Minuten")
        
    except Exception as e:
        print(f"❌ System Info Fehler: {e}")
    
    print()

def interactive_servo_control():
    """Interaktive Servo-Steuerung"""
    print("🎮 Interaktive Servo-Steuerung")
    print("Befehle: 'up', 'down', 'quit'")
    
    try:
        servo = GPIO.PWM(SERVO_PIN, 50)
        servo.start(0)
        
        while True:
            command = input(">>> ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'up':
                print("🔒 Bügel hoch...")
                GPIO.output(LED_BLUE, GPIO.HIGH)
                servo.ChangeDutyCycle(SERVO_UP)
                time.sleep(1)
                servo.ChangeDutyCycle(0)
                GPIO.output(LED_BLUE, GPIO.LOW)
                GPIO.output(LED_GREEN, GPIO.HIGH)
            elif command == 'down':
                print("🔓 Bügel runter...")
                GPIO.output(LED_BLUE, GPIO.HIGH)
                servo.ChangeDutyCycle(SERVO_DOWN)
                time.sleep(1)
                servo.ChangeDutyCycle(0)
                GPIO.output(LED_BLUE, GPIO.LOW)
                GPIO.output(LED_GREEN, GPIO.HIGH)
            else:
                print("❓ Unbekannter Befehl. Nutze: 'up', 'down', 'quit'")
        
        servo.stop()
        
    except Exception as e:
        print(f"❌ Interaktiver Test Fehler: {e}")

def main():
    """Hauptfunktion für Hardware-Tests"""
    print("🍓 Smart Parking Barrier - Hardware Test")
    print("=" * 50)
    
    try:
        setup_gpio()
        
        # Alle Tests durchführen
        test_system_info()
        test_internet()
        test_4g_stick()
        test_leds()
        test_servo()
        
        # Interaktiver Modus anbieten
        answer = input("🎮 Interaktive Servo-Steuerung starten? (y/n): ")
        if answer.lower() in ['y', 'yes', 'j', 'ja']:
            interactive_servo_control()
        
        print("🎉 Hardware-Test abgeschlossen!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test durch Benutzer gestoppt")
    except Exception as e:
        print(f"❌ Test Fehler: {e}")
    finally:
        # Cleanup
        GPIO.output(LED_GREEN, GPIO.LOW)
        GPIO.output(LED_RED, GPIO.LOW)
        GPIO.output(LED_BLUE, GPIO.LOW)
        GPIO.cleanup()

if __name__ == "__main__":
    main()
