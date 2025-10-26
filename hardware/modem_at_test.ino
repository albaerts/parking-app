#include <Arduino.h>
// Minimaler AT-Test für SIM7600 über UART2
// Verkabelung:
//   Hinweis: "RX2/TX2" sind die zweite UART des ESP32 (Serial2) – es sind keine festen Pins am Board!
//   Du kannst beliebige geeignete GPIOs für Serial2 wählen. Unten sind zwei gängige Optionen gezeigt.
//   Aktive Auswahl (siehe Defines MODEM_RX/MODEM_TX):
//   Modem TXD  -> ESP32 Serial2 RX (MODEM_RX GPIO)
//   Modem RXD  -> ESP32 Serial2 TX (MODEM_TX GPIO)
//   GND gemeinsam, 5V separat versorgen
// Bedienung:
//   - Seriellen Monitor öffnen (115200)
//   - 'AT' eintippen und Enter (oder 'AT+CPIN?')
//   - Erwartete Antwort: OK
//   - Zeilenende im Monitor darf CR, LF oder CRLF sein – wird automatisch zu CRLF normalisiert

#define BAUD_PC    115200  // Baudrate für PC <-> ESP32 (Serieller Monitor)
// Start-Baudrate fürs Modem: Nutzer meldete "OK" bei 57600
#define BAUD_MODEM 57600   // Baudrate für ESP32 <-> Modem (Serial2)

// --- UART2-Pins festlegen ---
// Option A (DevKit Standard):
//   #define MODEM_RX 16  // ESP32 empfängt hier (an Modem TXD)
//   #define MODEM_TX 17  // ESP32 sendet hier (an Modem RXD)
// Option B (weit verbreitet und oft frei):
#define MODEM_RX 27    // ESP32 empfängt hier (an Modem TXD)
#define MODEM_TX 26    // ESP32 sendet hier (an Modem RXD)

// Sicherheit: UART0-Pins (GPIO3=RX0, GPIO1=TX0) nicht fürs Modem verwenden!
#if (MODEM_RX == 3) || (MODEM_TX == 1)
#error "Bitte nicht RX0 (GPIO3) / TX0 (GPIO1) für das Modem nutzen – das stört Upload & Monitor."
#endif

bool g_muteModemOut = false; // '!' im PC-Terminal toggelt Modem->PC Ausgabe

// Laufzeit-Baudumschaltung für das Modem (Serial2)
const uint32_t BAUD_LIST[] = {115200, 9600, 57600, 38400, 230400};
const size_t   BAUD_LIST_LEN = sizeof(BAUD_LIST) / sizeof(BAUD_LIST[0]);
size_t         g_baudIndex = 0;
uint32_t       g_modemBaud = BAUD_MODEM;

void applyModemBaud(uint32_t rate) {
  g_modemBaud = rate;
  Serial2.end();
  delay(50);
  Serial2.begin(g_modemBaud, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(50);
  Serial.println("[AT-TEST] Modem-Baud jetzt: " + String(g_modemBaud));
}

void flushAndEcho() {
  unsigned long t0 = millis();
  while (millis() - t0 < 300) {
    if (Serial2.available()) {
      int c = Serial2.read();
      Serial.write(c);
    }
  }
}

void setup() {
  Serial.begin(BAUD_PC);
  delay(200);
  // passenden Index für Start-Baud finden
  for (size_t i = 0; i < BAUD_LIST_LEN; ++i) {
    if (BAUD_LIST[i] == BAUD_MODEM) { g_baudIndex = i; break; }
  }
  Serial.println("\n[AT-TEST] Starte Serial2 auf " + String(BAUD_MODEM) + ", Pins RX=" + String(MODEM_RX) + ", TX=" + String(MODEM_TX));
  Serial2.begin(BAUD_MODEM, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(300);

  // Kleiner Weckruf an das Modem
  Serial2.print("AT\r\n");
  delay(200);
  flushAndEcho();

  Serial.println("Tippe AT-Befehle unten ein. Beispiele: AT, AT+CPIN?, AT+CSQ, AT+CREG?, AT+CGATT?\n");
  Serial.println("Hinweis: '!' im Terminal toggelt Anzeige des Modem-Outputs (Mute/Unmute).");
  Serial.println("        '#' schaltet die Modem-Baudrate durch: 115200 → 9600 → 57600 → 38400 → 230400 → ...");
  Serial.println("        'F' setzt ATE0, fixiert 115200 (AT+IPR), speichert (AT&W) und schaltet Sketch auf 115200 um.");
  Serial.println("        'R' rebootet das Modem (AT+CFUN=1,1). ");
  Serial.println("        '?' zeigt diese Hilfe erneut.\n");
}

void loop() {
  // PC -> Modem
  if (Serial.available()) {
    int c = Serial.read();
    // '!' als lokale Steuerung: Modem-Ausgabe muten/unmuten
    if (c == '!') {
      g_muteModemOut = !g_muteModemOut;
      Serial.println(g_muteModemOut ? "\n[AT-TEST] Modem-Output: MUTE\n" : "\n[AT-TEST] Modem-Output: UNMUTE\n");
      return; // Nicht an Modem weiterleiten
    }
    // '#' Baudrate zyklisch umschalten (nur Modem-Link)
    if (c == '#') {
      g_baudIndex = (g_baudIndex + 1) % BAUD_LIST_LEN;
      applyModemBaud(BAUD_LIST[g_baudIndex]);
      return;
    }
    // '?' Hilfe
    if (c == '?') {
      Serial.println("\n[AT-TEST] Hilfe:\n  !  -> Mute/Unmute Modem-Output\n  #  -> Modem-Baudrate umschalten\n  F  -> ATE0; AT+IPR=115200; AT&W; Sketch auf 115200 umschalten\n  R  -> Modem reboot (AT+CFUN=1,1)\n  ?  -> Hilfe anzeigen\n  AT -> Befehl an Modem (mit CR/LF)");
      return;
    }
    // 'F' Fast-Setup: Echo aus, feste Baud 115200 setzen, speichern und Sketch-Baud umstellen
    if (c == 'F' || c == 'f') {
      Serial.println("\n[AT-TEST] Setze ATE0, AT+IPR=115200, AT&W und wechsle auf 115200 …");
      Serial2.print("ATE0\r\n");
      delay(150);
      flushAndEcho();
      Serial2.print("AT+IPR=115200\r\n");
      delay(200);
      flushAndEcho();
      Serial2.print("AT&W\r\n");
      delay(200);
      flushAndEcho();
      applyModemBaud(115200);
      return;
    }
    // 'R' Modem neu starten
    if (c == 'R' || c == 'r') {
      Serial.println("\n[AT-TEST] Sende AT+CFUN=1,1 (Reboot) …");
      Serial2.print("AT+CFUN=1,1\r\n");
      return;
    }
    // Zeilenenden robust behandeln: CR, LF oder CRLF -> immer CRLF zum Modem
    if (c == '\r' || c == '\n') {
      Serial2.write('\r');
      Serial2.write('\n');
      // Lokales Echo, damit im Monitor sichtbar ist, dass gesendet wurde
      Serial.write('\r');
      Serial.write('\n');
    } else {
      Serial2.write(c);
      // Zeichen lokal zurückspiegeln
      Serial.write(c);
    }
  }
  // Modem -> PC
  if (Serial2.available()) {
    int c = Serial2.read();
    if (!g_muteModemOut) {
      Serial.write(c);
    }
  }
}
