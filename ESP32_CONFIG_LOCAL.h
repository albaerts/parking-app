/*
 * ESP32 Smart Parking - Lokale Konfiguration
 * 
 * Diese Datei enthält deine persönlichen Einstellungen für:
 * - WiFi-Verbindung
 * - Server-Verbindung (lokal)
 * - Hardware-ID für dein Gerät
 * 
 * ANLEITUNG:
 * 1. Kopiere diese Datei ins gleiche Verzeichnis wie die .ino Datei
 * 2. Passe die Werte unten an
 * 3. In der .ino Datei: #include "ESP32_CONFIG_LOCAL.h" ganz oben hinzufügen
 * 4. Hochladen auf ESP32
 */

// ========== WIFI EINSTELLUNGEN ==========
// Ersetze mit deinen WiFi-Zugangsdaten
const char* WIFI_SSID = "DEIN_WIFI_NAME";
const char* WIFI_PASSWORD = "DEIN_WIFI_PASSWORT";

// ========== SERVER EINSTELLUNGEN ==========
// Für SIM7600 LTE: Produktions-Server (öffentlich erreichbar)
// WICHTIG: Muss von überall erreichbar sein (nicht localhost!)
// 
// Für lokale Tests: Nutze ngrok oder ähnliches für öffentliche URL
// Für Produktion: api.gashis.ch
const char* PRODUCTION_API_BASE = "https://api.gashis.ch";
// Für lokale Entwicklung: Deine Computer-IP-Adresse
// WICHTIG: Nicht "localhost" verwenden! ESP32 braucht die echte IP
// 
// So findest du deine IP:
// macOS: System Preferences → Network → deine IP steht dort
// oder Terminal: ifconfig | grep "inet " | grep -v 127.0.0.1
//
// Beispiel: "http://192.168.1.100:8000"
const char* LOCAL_API_BASE = "http://192.168.1.255:8000";

// ========== HARDWARE-ID ==========
// Dies ist die eindeutige ID für dein Gerät
// Du hast diese bereits in der Web-App bei "Device zuweisen" verwendet
const char* DEVICE_ID = "PARK_DEVICE_001";

// Optional: Für Produktion später (aktuell nicht verwendet)
const char* PRODUCTION_API_BASE = "https://api.gashis.ch/api";

// ========== HARDWARE PINS ==========
// ESP32 + SIM7600 + Hall Sensor + Servo SG92R
// Diese sollten zu deinem Aufbau passen

// Hall-Sensor (Magnetsensor) - z.B. A3144E oder ähnlich
#define HALL_SENSOR_PIN 32  // GPIO32 (ADC1_CH4)

// Servo SG92R (Parkbügel)
#define SERVO_PIN 25        // GPIO25 (PWM-fähig)

// SIM7600 (falls du 4G/LTE nutzt, aktuell auf WiFi)
// Diese sind nur für Referenz, falls du später umsteigst
#define SIM7600_TX 17       // TX vom ESP32 zu RX vom SIM7600
#define SIM7600_RX 16       // RX vom ESP32 zu TX vom SIM7600
#define SIM7600_PWRKEY 4    // Power Key Pin

// Optional: Status LED
#define STATUS_LED 2        // Eingebaute LED auf ESP32

// ========== TIMING EINSTELLUNGEN ==========
// Wie oft soll das Gerät mit dem Server kommunizieren?
const unsigned long POLL_INTERVAL_MS = 10000;      // Commands abholen: alle 10 Sekunden
const unsigned long TELEMETRY_INTERVAL_MS = 30000;  // Telemetrie senden: alle 30 Sekunden

// ========== SERVO EINSTELLUNGEN ==========
// Kalibrierung für SG92R Servo
// Diese Werte musst du eventuell anpassen, je nach Montage
const int SERVO_POS_DOWN = 0;      // Bügel unten (Grad)
const int SERVO_POS_UP = 90;       // Bügel oben (Grad)
const int SERVO_SPEED_MS = 1000;   // Bewegungszeit in ms

// ========== SENSOR EINSTELLUNGEN ==========
// Hall-Sensor Schwellwert
// Wenn ein Magnet (Auto) erkannt wird, ändert sich der Wert
// Du musst diesen Wert experimentell ermitteln
const int HALL_THRESHOLD = 500;    // Startwert, wird automatisch kalibriert

// Kalibrierung beim Start durchführen?
const bool AUTO_CALIBRATE = true;

// ========== DEBUG EINSTELLUNGEN ==========
// Soll das Gerät ausführliche Debug-Ausgaben über Serial machen?
const bool DEBUG_VERBOSE = true;
const long SERIAL_BAUD = 115200;
