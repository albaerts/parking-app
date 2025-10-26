#!/usr/bin/env python3
"""
Smart Parking Barrier - Raspberry Pi Controller
Prototyp für Zürich Smart Parking System

Hardware:
- Raspberry Pi 4B
- SG90 Servo (Mini-Parkbügel)
- Huawei E3372 4G USB-Stick
- Anker PowerBank 20000mAh
- Status LEDs

Features:
- Servo-gesteuerte Mini-Barriere (hoch/runter)
- 4G Internetverbindung
- API-Integration zu FastAPI Backend
- Status-LEDs für visuelles Feedback
- Automatische Reconnection
- Error Handling & Logging
"""

import RPi.GPIO as GPIO
import time
import requests
import json
import logging
import threading
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# ========== GPIO PIN CONFIGURATION ==========
SERVO_PIN = 18        # PWM für SG90 Servo (GPIO18)
LED_GREEN = 23        # System OK (GPIO23)
LED_RED = 24          # Error/Wartung (GPIO24) 
LED_BLUE = 25         # Bügel in Bewegung (GPIO25)

# ========== SERVO CONFIGURATION ==========
# PWM Duty Cycle für SG90 Servo (50Hz)
SERVO_DOWN = 2.5      # 0° - Bügel horizontal (Parkplatz frei)
SERVO_UP = 12.5       # 180° - Bügel vertikal (Parkplatz blockiert)

# ========== SYSTEM CONFIGURATION ==========
DEVICE_ID = "PROTOTYPE_ZH_001"
API_BASE_URL = "http://localhost:8000"  # Deine FastAPI Backend URL
HEARTBEAT_INTERVAL = 30  # Sekunden zwischen Server-Abfragen
MAX_RETRIES = 3
CONNECTION_TIMEOUT = 10

# ========== LOGGING SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/parking_barrier.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ParkingBarrier:
    def __init__(self):
        """Initialize Parking Barrier Controller"""
        self.is_running = False
        self.barrier_position = "DOWN"  # DOWN (frei) oder UP (blockiert)
        self.last_heartbeat = None
        self.connection_status = False
        
        # Hardware initialisieren
        self._setup_gpio()
        self._setup_servo()
        
        logger.info(f"🚀 Parking Barrier {DEVICE_ID} initialisiert")
        
    def _setup_gpio(self):
        """GPIO Pins konfigurieren"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Servo PWM Pin
            GPIO.setup(SERVO_PIN, GPIO.OUT)
            
            # LED Pins
            GPIO.setup(LED_GREEN, GPIO.OUT)
            GPIO.setup(LED_RED, GPIO.OUT)
            GPIO.setup(LED_BLUE, GPIO.OUT)
            
            # LEDs initial ausschalten
            GPIO.output(LED_GREEN, GPIO.LOW)
            GPIO.output(LED_RED, GPIO.LOW)
            GPIO.output(LED_BLUE, GPIO.LOW)
            
            logger.info("✅ GPIO Pins erfolgreich konfiguriert")
            
        except Exception as e:
            logger.error(f"❌ GPIO Setup Fehler: {e}")
            raise
            
    def _setup_servo(self):
        """Servo PWM initialisieren"""
        try:
            self.servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz für SG90
            self.servo.start(0)  # Start mit 0% Duty Cycle
            
            # Initial Position: Bügel runter (frei)
            self._move_servo(SERVO_DOWN)
            time.sleep(1)
            self.servo.ChangeDutyCycle(0)  # PWM stoppen um Servo zu entspannen
            
            logger.info("✅ Servo erfolgreich initialisiert (Position: DOWN)")
            
        except Exception as e:
            logger.error(f"❌ Servo Setup Fehler: {e}")
            raise
    
    def _move_servo(self, position: float):
        """Servo zu spezifischer Position bewegen"""
        try:
            self.servo.ChangeDutyCycle(position)
            time.sleep(0.5)  # Zeit für Bewegung
            self.servo.ChangeDutyCycle(0)  # PWM stoppen
            
        except Exception as e:
            logger.error(f"❌ Servo Bewegung Fehler: {e}")
    
    def _set_led_status(self, green: bool = False, red: bool = False, blue: bool = False):
        """LED Status setzen"""
        GPIO.output(LED_GREEN, GPIO.HIGH if green else GPIO.LOW)
        GPIO.output(LED_RED, GPIO.HIGH if red else GPIO.LOW)
        GPIO.output(LED_BLUE, GPIO.HIGH if blue else GPIO.LOW)
    
    def _blink_led(self, pin: int, times: int = 3, delay: float = 0.3):
        """LED blinken lassen"""
        def blink():
            for _ in range(times):
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(delay)
        
        threading.Thread(target=blink, daemon=True).start()
    
    def raise_barrier(self) -> bool:
        """Bügel hochfahren (Parkplatz blockieren)"""
        if self.barrier_position == "UP":
            logger.info("🔒 Bügel bereits oben")
            return True
            
        try:
            logger.info("🔒 Bügel wird hochgefahren...")
            self._set_led_status(blue=True)  # Blaue LED während Bewegung
            
            self._move_servo(SERVO_UP)
            self.barrier_position = "UP"
            
            # Status LEDs: Grün + kurz 3x blinken
            self._set_led_status(green=True)
            self._blink_led(LED_BLUE, 3)
            
            logger.info("✅ Bügel erfolgreich hochgefahren")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Hochfahren: {e}")
            self._set_led_status(red=True)
            return False
    
    def lower_barrier(self) -> bool:
        """Bügel runterfahren (Parkplatz freigeben)"""
        if self.barrier_position == "DOWN":
            logger.info("🔓 Bügel bereits unten")
            return True
            
        try:
            logger.info("🔓 Bügel wird runtergefahren...")
            self._set_led_status(blue=True)  # Blaue LED während Bewegung
            
            self._move_servo(SERVO_DOWN)
            self.barrier_position = "DOWN"
            
            # Status LEDs: Grün + kurz 1x blinken
            self._set_led_status(green=True)
            self._blink_led(LED_BLUE, 1)
            
            logger.info("✅ Bügel erfolgreich runtergefahren")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Runterfahren: {e}")
            self._set_led_status(red=True)
            return False
    
    def check_internet_connection(self) -> bool:
        """Internetverbindung prüfen"""
        try:
            # Ping Google DNS
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '3', '8.8.8.8'], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
            
        except Exception as e:
            logger.warning(f"⚠️ Internet-Check Fehler: {e}")
            return False
    
    def send_heartbeat(self) -> bool:
        """Heartbeat an Server senden"""
        try:
            # Status-Daten sammeln
            status_data = {
                "device_id": DEVICE_ID,
                "timestamp": datetime.now().isoformat(),
                "barrier_position": self.barrier_position,
                "location": {
                    "lat": 47.3769,  # Zürich Koordinaten (Fallback)
                    "lng": 8.5417
                },
                "system_status": {
                    "uptime": time.time(),
                    "temperature": self._get_cpu_temperature(),
                    "memory_usage": self._get_memory_usage()
                }
            }
            
            # HTTP Request an Backend
            response = requests.post(
                f"{API_BASE_URL}/api/barrier/heartbeat",
                json=status_data,
                timeout=CONNECTION_TIMEOUT
            )
            
            if response.status_code == 200:
                self.connection_status = True
                self.last_heartbeat = datetime.now()
                logger.info("💓 Heartbeat erfolgreich gesendet")
                return True
            else:
                logger.warning(f"⚠️ Heartbeat Fehler: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Heartbeat Verbindungsfehler: {e}")
            self.connection_status = False
            return False
        except Exception as e:
            logger.error(f"❌ Heartbeat Fehler: {e}")
            return False
    
    def check_server_commands(self) -> bool:
        """Server nach neuen Befehlen abfragen"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/barrier/{DEVICE_ID}/command",
                timeout=CONNECTION_TIMEOUT
            )
            
            if response.status_code == 200:
                command_data = response.json()
                command = command_data.get('command', '').upper()
                
                if command == 'UP' and self.barrier_position == "DOWN":
                    logger.info("📡 Server-Befehl empfangen: BÜGEL HOCH")
                    return self.raise_barrier()
                    
                elif command == 'DOWN' and self.barrier_position == "UP":
                    logger.info("📡 Server-Befehl empfangen: BÜGEL RUNTER")
                    return self.lower_barrier()
                    
                elif command == 'STATUS':
                    logger.info("📡 Status-Anfrage empfangen")
                    return True
                    
                else:
                    logger.debug(f"📡 Kein neuer Befehl (aktuell: {command})")
                    return True
                    
            elif response.status_code == 404:
                logger.debug("📡 Keine Befehle verfügbar")
                return True
            else:
                logger.warning(f"⚠️ Command-Check Fehler: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Command-Check Verbindungsfehler: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Command-Check Fehler: {e}")
            return False
    
    def _get_cpu_temperature(self) -> float:
        """CPU Temperatur auslesen"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                return round(temp, 1)
        except:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """RAM Nutzung in % auslesen"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                
            mem_total = int([l for l in lines if 'MemTotal' in l][0].split()[1])
            mem_free = int([l for l in lines if 'MemFree' in l][0].split()[1])
            mem_used = mem_total - mem_free
            
            return round((mem_used / mem_total) * 100, 1)
        except:
            return 0.0
    
    def run_main_loop(self):
        """Hauptschleife des Parkbügel-Controllers"""
        logger.info("🚀 Hauptschleife gestartet")
        self.is_running = True
        
        # Initial Status: Grüne LED an
        self._set_led_status(green=True)
        
        last_heartbeat_time = 0
        error_count = 0
        
        try:
            while self.is_running:
                current_time = time.time()
                
                # Internet-Verbindung prüfen
                if not self.check_internet_connection():
                    logger.warning("⚠️ Keine Internetverbindung")
                    self._set_led_status(red=True)
                    time.sleep(10)
                    continue
                
                # Heartbeat senden (alle 30 Sekunden)
                if current_time - last_heartbeat_time >= HEARTBEAT_INTERVAL:
                    if self.send_heartbeat():
                        error_count = 0
                        self._set_led_status(green=True)
                    else:
                        error_count += 1
                        if error_count >= MAX_RETRIES:
                            self._set_led_status(red=True)
                    
                    last_heartbeat_time = current_time
                
                # Server-Befehle prüfen
                self.check_server_commands()
                
                # Kurz warten vor nächster Iteration
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("🛑 Hauptschleife durch Benutzer gestoppt")
        except Exception as e:
            logger.error(f"❌ Fehler in Hauptschleife: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """System sauber herunterfahren"""
        logger.info("🛑 System wird heruntergefahren...")
        self.is_running = False
        
        try:
            # Bügel in sichere Position (runter)
            if self.barrier_position == "UP":
                self.lower_barrier()
            
            # LEDs ausschalten
            self._set_led_status()
            
            # Servo stoppen
            self.servo.stop()
            
            # GPIO cleanup
            GPIO.cleanup()
            
            logger.info("✅ System sauber heruntergefahren")
            
        except Exception as e:
            logger.error(f"❌ Shutdown Fehler: {e}")

def main():
    """Hauptfunktion"""
    print("🍓 Smart Parking Barrier - Raspberry Pi Controller")
    print(f"📍 Device ID: {DEVICE_ID}")
    print(f"🌐 Backend URL: {API_BASE_URL}")
    print("=" * 50)
    
    try:
        # Parkbügel-Controller erstellen und starten
        barrier = ParkingBarrier()
        
        # Hauptschleife starten
        barrier.run_main_loop()
        
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
