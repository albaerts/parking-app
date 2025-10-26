/*
  Smart Parking – All-in-One (ESP32 + SIM7600G-H)

  Funktionen
  - SG92R/SG90 Servo zur Barrierensteuerung (GPIO 18)
  - Hall-Sensor (GPIO 19, Pull-up)
  - Status-LED (GPIO 2, optional)
  - Mobilfunk-HTTP über SIM7600 (TinyGSM) → POST /parking-spots/{id}/status

  Hardware-Hinweise
  - SIM7600 benötigt eine stabile 5–9 V Versorgung mit genügend Strom (ca. 2 A Spitzenstrom).
  - UART: Standard-AT-Port des SIM7600 an ESP32 UART (z. B. GPIO 16/17) anschließen.
  - Alle Massen (GND) verbinden: ESP32, Servo, Modem, Versorgung.

  Bibliotheken
  - TinyGSM (aktuelle Version)
  - ESP32Servo
*/

// Aktivieren, damit TinyGsmClientSecure verfügbar ist (HTTPS über Modem-TLS)
#ifndef TINY_GSM_USE_SSL
#define TINY_GSM_USE_SSL 1
#endif
#define TINY_GSM_MODEM_SIM7600
#include <TinyGsmClient.h>
#include <ArduinoHttpClient.h>
#include <ESP32Servo.h>

// ----- Pins -----
const int SERVO_PIN = 18;
const int HALL_PIN  = 19;
const int LED_PIN   = 2;   // optional

// UART zum SIM7600 (an dein Wiring anpassen)
// Üblich: UART-Pins frei wählbar; passend zum AT-Test-Sketch nutzen wir IO27/IO26:
// SIM7600 TXD → ESP32 RX (GPIO27), SIM7600 RXD ← ESP32 TX (GPIO26)
#define MODEM_RX 27
#define MODEM_TX 26

// ----- Angles -----
const int CLOSED_ANGLE = 110;
const int OPEN_ANGLE   = 20;

// Hall-Logik
const bool HALL_LOW_IS_OCCUPIED = true;
const uint32_t OCCUPIED_CONFIRM_MS = 200;
const uint32_t FREE_CONFIRM_MS = 400;

// ----- Mobilfunk-Konfiguration -----
// APN-Daten deines Providers eintragen
// Swisscom (CH): gprs.swisscom.ch, meist ohne User/Pass
const char APN[]       = "gprs.swisscom.ch"; // Swisscom APN
const char GPRS_USER[] = "";
const char GPRS_PASS[] = "";
// Optional: SIM PIN, falls aktiv. Leer lassen, wenn kein PIN gesetzt.
const char SIM_PIN[]   = "8115";

// Backend
// Wichtig: Backend muss öffentlich erreichbar sein (oder via Tunnel)
// HTTPS empfohlen: USE_HTTPS = 1 und Port 443 verwenden
// Einfachste Variante: Plain HTTP verwenden -> USE_HTTPS = 0 und Port 80
#define USE_HTTPS 0
// Hinweis: TinyGSM bietet für SIM7600 keinen TinyGsmClientSecure.
// Wir nutzen für HTTPS die SIM7600-HTTP(S)-AT-Befehle (AT+HTTPSSL/HTTPACTION/...)
// Hinweis: Für die einfache HTTP-Variante setze hier deine öffentliche HTTP-Endpoint-Domain/IP.
// Beispiele:
// - Öffentlicher Server (VPS):   SERVER_HOST="<deine-ip-oder-domain>", SERVER_PORT=80
// - ngrok TCP (lokal weiterleiten): SERVER_HOST="<X>.tcp.ngrok.io", SERVER_PORT=<Port>
const char SERVER_HOST[] = "example.com"; // bitte anpassen
const int  SERVER_PORT   = USE_HTTPS ? 443 : 80; // 443 für HTTPS, 80 für HTTP
int PARKING_SPOT_ID = 1;

HardwareSerial Modem(1);
TinyGsm modem(Modem);
TinyGsmClient netClient(modem);

// ---- SIM7600 HTTPS (AT+HTTP*) Helpers ----

// Track if we already rebooted the modem via CFUN to avoid redundant restarts
bool g_modemRecentlyRebooted = false;

// Resolve hostname using SIM7600 DNS for diagnostics
bool resolveHost(const String& host) {
  Serial.print("[DNS] Resolving "); Serial.println(host);
  String resp;
  // Clear buffer and send query
  while (Modem.available()) Modem.read();
  Modem.print(String("AT+CDNSGIP=\"") + host + "\"\r\n");
  // Expect lines with +CDNSGIP: responses; allow up to ~20s
  uint32_t start = millis();
  bool any = false;
  while (millis() - start < 20000) {
    while (Modem.available()) {
      char c = (char)Modem.read();
      resp += c;
      if (resp.indexOf("+CDNSGIP:") != -1) any = true;
      if (resp.indexOf("\r\nOK\r\n") != -1 || resp.indexOf("\r\nERROR\r\n") != -1) {
        Serial.print("[DNS] Response: "); Serial.println(resp);
        return any && (resp.indexOf("\r\nERROR\r\n") == -1);
      }
    }
    delay(20);
  }
  Serial.println("[DNS] Timeout waiting for DNS response");
  return false;
}

bool atSendAndWaitOK(const String& cmd, uint32_t timeoutMs = 5000) {
  while (Modem.available()) Modem.read();
  Modem.print(cmd); Modem.print("\r\n");
  uint32_t start = millis();
  String buf;
  while (millis() - start < timeoutMs) {
    while (Modem.available()) {
      char c = (char)Modem.read();
      buf += c;
      if (buf.indexOf("\r\nOK\r\n") != -1 || buf.endsWith("\nOK\r\n")) return true;
      if (buf.indexOf("\r\nERROR\r\n") != -1) return false;
    }
    delay(5);
  }
  return false;
}

// Send AT command and capture full response until final OK/ERROR or timeout
bool atSendAndGetResponse(const String& cmd, String& out, uint32_t timeoutMs = 5000) {
  out = "";
  while (Modem.available()) Modem.read();
  Modem.print(cmd); Modem.print("\r\n");
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    while (Modem.available()) {
      char c = (char)Modem.read();
      out += c;
      if (out.indexOf("\r\nOK\r\n") != -1 || out.endsWith("\nOK\r\n")) return true;
      if (out.indexOf("\r\nERROR\r\n") != -1) return false;
    }
    delay(5);
  }
  return false;
}

// Persist SIM7600 UART and echo settings for reliability
bool persistModemSettings() {
  Serial.println("[MODEM] Persisting UART settings (ATE0, IPR=115200, AT&W, reboot)...");
  // Disable echo
  atSendAndWaitOK("ATE0");
  // Set fixed UART speed 115200 (safe if already 115200)
  bool ok = atSendAndWaitOK("AT+IPR=115200");
  if (!ok) Serial.println("[MODEM] AT+IPR failed (continuing)...");
  // Save profile
  atSendAndWaitOK("AT&W");
  // Reboot RF/functionality so new IPR persists and stack is clean
  atSendAndWaitOK("AT+CFUN=1,1");
  g_modemRecentlyRebooted = true;
  // Wait for modem to come back and resync UART
  delay(7000); // SIM7600 can take several seconds to be ready after CFUN
  // Re-initialize UART at 115200 to match persisted setting
  Modem.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
  // Probe until AT answers
  uint32_t start = millis();
  while (millis() - start < 15000) {
    if (modem.testAT(800)) {
      Serial.println("[MODEM] Re-synced at 115200 after reboot.");
      return true;
    }
    delay(250);
  }
  Serial.println("[MODEM] Could not resync after persisting settings. Falling back to auto-baud...");
  return initModemUARTAutoBaud();
}

// Run quick AT health checks for diagnostics
void runBasicATHealth() {
  String resp;
  Serial.println("[AT] ATI (modem info)");
  if (atSendAndGetResponse("ATI", resp, 3000)) Serial.println(resp);
  else Serial.println("[AT] ATI failed");

  resp = "";
  Serial.println("[AT] AT+CPIN? (SIM)");
  if (atSendAndGetResponse("AT+CPIN?", resp, 3000)) Serial.println(resp);
  else Serial.println("[AT] CPIN? failed");

  resp = "";
  Serial.println("[AT] AT+CSQ (signal)");
  if (atSendAndGetResponse("AT+CSQ", resp, 3000)) Serial.println(resp);
  else Serial.println("[AT] CSQ failed");

  resp = "";
  Serial.println("[AT] AT+CEREG? (LTE reg)");
  if (atSendAndGetResponse("AT+CEREG?", resp, 3000)) Serial.println(resp);
  else Serial.println("[AT] CEREG? failed");

  resp = "";
  Serial.println("[AT] AT+CGATT? (GPRS attach)");
  if (atSendAndGetResponse("AT+CGATT?", resp, 3000)) Serial.println(resp);
  else Serial.println("[AT] CGATT? failed");
}

// Unlock SIM if CPIN reports SIM PIN and SIM_PIN is set
void unlockSIMIfNeeded() {
  String resp;
  if (atSendAndGetResponse("AT+CPIN?", resp, 3000)) {
    if (resp.indexOf("+CPIN: SIM PIN") != -1) {
      if (strlen(SIM_PIN) > 0) {
        Serial.println("[MODEM] SIM requires PIN, sending CPIN...");
        String cmd = String("AT+CPIN=\"") + SIM_PIN + "\"";
        if (!atSendAndWaitOK(cmd, 10000)) {
          Serial.println("[MODEM] CPIN entry failed");
        } else {
          // Give time for SIM to transition to READY
          delay(3000);
        }
      } else {
        Serial.println("[MODEM] SIM PIN required but SIM_PIN not set.");
      }
    }
  }
}

// Wait until SIM is ready (CPIN: READY) and optionally registration usable
bool waitForSIMReady(uint32_t timeoutMs = 30000) {
  Serial.print("[MODEM] Waiting for SIM ready...");
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    String resp;
    if (atSendAndGetResponse("AT+CPIN?", resp, 1500)) {
      if (resp.indexOf("+CPIN: READY") != -1) {
        Serial.println(" OK");
        return true;
      }
    }
    Serial.print(".");
    delay(500);
  }
  Serial.println(" fail");
  return false;
}

bool waitForRegistration(uint32_t timeoutMs = 45000) {
  Serial.print("[MODEM] Waiting for registration...");
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    String resp;
    if (atSendAndGetResponse("AT+CEREG?", resp, 1500)) {
      // +CEREG: <n>,<stat>,...
      // stat 1=home, 5=roaming
      int statPos = resp.indexOf(",");
      if (statPos != -1 && statPos + 2 < (int)resp.length()) {
        int stat = resp.substring(statPos + 1, statPos + 2).toInt();
        if (stat == 1 || stat == 5) {
          Serial.println(" OK");
          return true;
        }
      }
    }
    Serial.print(".");
    delay(700);
  }
  Serial.println(" fail");
  return false;
}

bool atWaitFor(const String& needle, String& out, uint32_t timeoutMs = 15000) {
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    while (Modem.available()) {
      char c = (char)Modem.read();
      out += c;
      if (out.indexOf(needle) != -1) return true;
      if (out.indexOf("\r\nERROR\r\n") != -1) return false;
    }
    delay(5);
  }
  return false;
}

// Wait for a complete URC line that contains the given prefix and ends with CRLF
bool atWaitForURCLine(const String& prefix, String& lineOut, uint32_t timeoutMs = 15000) {
  lineOut = "";
  String buf;
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    while (Modem.available()) {
      char c = (char)Modem.read();
      buf += c;
      int pos = buf.indexOf(prefix);
      if (pos != -1) {
        int eol = buf.indexOf("\r\n", pos);
        if (eol != -1) {
          lineOut = buf.substring(pos, eol);
          return true;
        }
      }
      if (buf.indexOf("\r\nERROR\r\n") != -1) { lineOut = buf; return false; }
    }
    delay(5);
  }
  lineOut = buf;
  return false;
}

bool httpInitHTTPS() {
  // Terminate any previous session
  Modem.print("AT+HTTPTERM\r\n");
  delay(50);
  // Configure SSL context 0: no cert verification, TLS1.2, SNI on
  atSendAndWaitOK("AT+CSSLCFG=\"authmode\",0,0");
  atSendAndWaitOK("AT+CSSLCFG=\"sslversion\",0,3");
  atSendAndWaitOK("AT+CSSLCFG=\"SNI\",0,1");
  // Init HTTP
  if (!atSendAndWaitOK("AT+HTTPINIT")) return false;
  if (!atSendAndWaitOK("AT+HTTPSSL=1")) return false; // enable HTTPS
  if (!atSendAndWaitOK("AT+HTTPPARA=\"CID\",1")) return false; // PDP context 1
  // Optional: set UA to something common
  // atSendAndWaitOK("AT+HTTPPARA=\"UA\",\"ESP32-SIM7600\"");
  return true;
}

void httpTerm() {
  Modem.print("AT+HTTPTERM\r\n");
  // don't block here
}

bool httpGetHTTPS(const String& host, const String& path, int& statusCode, String& body) {
  statusCode = -1; body = "";
  if (!httpInitHTTPS()) return false;
  String url = String("https://") + host + path;
  Serial.print("[HTTPS-HTTP] URL: "); Serial.println(url);
  if (!atSendAndWaitOK(String("AT+HTTPPARA=\"URL\",\"") + url + "\"")) { Serial.println("[HTTPS-HTTP] URL set failed"); httpTerm(); return false; }
  // Set HOST header explicitly; some firmwares also use this for SNI
  atSendAndWaitOK(String("AT+HTTPPARA=\"HOST\",\"") + host + "\"");
  // Allow redirects if any
  atSendAndWaitOK("AT+HTTPPARA=\"REDIR\",1");
  if (!atSendAndWaitOK("AT+HTTPACTION=0")) { httpTerm(); return false; }
  // Wait for +HTTPACTION: 0,status,len
  String resp;
  if (!atWaitFor("+HTTPACTION:", resp, 30000)) { Serial.println("[HTTPS-HTTP] No ACTION URC"); httpTerm(); return false; }
  Serial.print("[HTTPS-HTTP] ACTION URC: "); Serial.println(resp);
  // Parse status code
  int idx = resp.indexOf("+HTTPACTION:");
  if (idx >= 0) {
    int comma1 = resp.indexOf(',', idx);
    int comma2 = comma1 >= 0 ? resp.indexOf(',', comma1 + 1) : -1;
    if (comma1 > 0 && comma2 > comma1) {
      statusCode = resp.substring(comma1 + 1, comma2).toInt();
    }
  }
  // Read body
  Modem.print("AT+HTTPREAD\r\n");
  String rd;
  if (!atWaitFor("+HTTPREAD:", rd, 15000)) { Serial.println("[HTTPS-HTTP] No READ URC"); httpTerm(); return false; }
  // Continue reading until end OK is received
  if (!atWaitFor("\r\nOK\r\n", rd, 15000)) { Serial.println("[HTTPS-HTTP] No final OK after READ"); httpTerm(); return false; }
  Serial.print("[HTTPS-HTTP] READ URC len+data snippet: "); Serial.println(rd.substring(0, 120));
  // +HTTPREAD: <len>\r\n<data>\r\nOK
  int hdr = rd.indexOf("+HTTPREAD:");
  if (hdr >= 0) {
    int nl = rd.indexOf("\n", hdr);
    if (nl > 0) {
      // data starts after this line; ensure we captured it
      int okPos = rd.lastIndexOf("\r\nOK\r\n");
      if (okPos > nl) {
        body = rd.substring(nl + 1, okPos);
      }
    }
  }
  httpTerm();
  return (statusCode > 0);
}

bool httpPostHTTPS(const String& host, const String& path, const String& contentType, const String& payload, int& statusCode, String& body) {
  statusCode = -1; body = "";
  if (!httpInitHTTPS()) return false;
  String url = String("https://") + host + path;
  Serial.print("[HTTPS-HTTP] URL: "); Serial.println(url);
  if (!atSendAndWaitOK(String("AT+HTTPPARA=\"URL\",\"") + url + "\"")) { Serial.println("[HTTPS-HTTP] URL set failed"); httpTerm(); return false; }
  // Set HOST header explicitly; some firmwares also use this for SNI
  atSendAndWaitOK(String("AT+HTTPPARA=\"HOST\",\"") + host + "\"");
  if (!atSendAndWaitOK(String("AT+HTTPPARA=\"CONTENT\",\"") + contentType + "\"")) { Serial.println("[HTTPS-HTTP] CONTENT set failed"); httpTerm(); return false; }
  // Provide data
  if (!atSendAndWaitOK(String("AT+HTTPDATA=") + payload.length() + ",10000")) { httpTerm(); return false; }
  // Wait for DOWNLOAD prompt
  String dl;
  if (!atWaitFor("DOWNLOAD", dl, 3000)) { Serial.println("[HTTPS-HTTP] No DOWNLOAD prompt"); httpTerm(); return false; }
  // Send payload then wait OK
  Modem.print(payload);
  if (!atWaitFor("OK", dl, 10000)) { Serial.println("[HTTPS-HTTP] No OK after payload"); httpTerm(); return false; }
  // POST action
  if (!atSendAndWaitOK("AT+HTTPACTION=1")) { httpTerm(); return false; }
  String resp;
  if (!atWaitFor("+HTTPACTION:", resp, 30000)) { Serial.println("[HTTPS-HTTP] No ACTION URC"); httpTerm(); return false; }
  Serial.print("[HTTPS-HTTP] ACTION URC: "); Serial.println(resp);
  int idx = resp.indexOf("+HTTPACTION:");
  if (idx >= 0) {
    int comma1 = resp.indexOf(',', idx);
    int comma2 = comma1 >= 0 ? resp.indexOf(',', comma1 + 1) : -1;
    if (comma1 > 0 && comma2 > comma1) {
      statusCode = resp.substring(comma1 + 1, comma2).toInt();
    }
  }
  // Read response body
  Modem.print("AT+HTTPREAD\r\n");
  String rd;
  if (!atWaitFor("+HTTPREAD:", rd, 15000)) { Serial.println("[HTTPS-HTTP] No READ URC"); httpTerm(); return false; }
  if (!atWaitFor("\r\nOK\r\n", rd, 15000)) { Serial.println("[HTTPS-HTTP] No final OK after READ"); httpTerm(); return false; }
  Serial.print("[HTTPS-HTTP] READ URC len+data snippet: "); Serial.println(rd.substring(0, 120));
  int hdr = rd.indexOf("+HTTPREAD:");
  if (hdr >= 0) {
    int nl = rd.indexOf("\n", hdr);
    if (nl > 0) {
      int okPos = rd.lastIndexOf("\r\nOK\r\n");
      if (okPos > nl) {
        body = rd.substring(nl + 1, okPos);
      }
    }
  }
  httpTerm();
  return (statusCode > 0);
}

// ---- SIM7600 CHTTPS (SNI-friendly) Fallback ----

bool chttpsStart() {
  Modem.print("AT+CHTTPSSTOP\r\n");
  delay(50);
  bool ok = atSendAndWaitOK("AT+CHTTPSSTART");
  // Configure CHTTPS SSL/TLS behavior: TLS1.2, no verify, enable SNI, ignore time skew
  atSendAndWaitOK("AT+CHTTPSCFG=\"sslversion\",3");
  atSendAndWaitOK("AT+CHTTPSCFG=\"verify\",0");
  atSendAndWaitOK("AT+CHTTPSCFG=\"sni\",1");
  atSendAndWaitOK("AT+CHTTPSCFG=\"ignorelocaltime\",1");
  return ok;
}

void chttpsStop() {
  Modem.print("AT+CHTTPSSTOP\r\n");
}

bool chttpsOpen(const String& host, int port = 443) {
  // Try to enable SNI if supported (best-effort; ignore failure)
  atSendAndWaitOK("AT+CSSLCFG=\"authmode\",0,0");
  atSendAndWaitOK("AT+CSSLCFG=\"sslversion\",0,3");
  atSendAndWaitOK("AT+CSSLCFG=\"SNI\",0,1");
  delay(30);
  String cmd = String("AT+CHTTPSOPSE=\"") + host + "\"," + port;
  if (!atSendAndWaitOK(cmd)) {
    Serial.println("[CHTTPS] OPSE command failed");
    return false;
  }
  // Wait for explicit URC with result code (up to 15s)
  String urcLine;
  if (!atWaitForURCLine("+CHTTPSOPSE:", urcLine, 15000)) {
    Serial.println("[CHTTPS] No OPSE URC received");
    return false;
  }
  Serial.print("[CHTTPS] OPSE URC: "); Serial.println(urcLine);
  // Expect formats like: "+CHTTPSOPSE: 0" or "+CHTTPSOPSE: 0,xx"
  int colon = urcLine.indexOf(':');
  if (colon == -1) return false;
  String rest = urcLine.substring(colon + 1);
  rest.trim();
  int comma = rest.indexOf(',');
  String codeStr = (comma >= 0) ? rest.substring(0, comma) : rest;
  codeStr.trim();
  int code = codeStr.toInt();
  if (code != 0) {
    Serial.print("[CHTTPS] OPSE failed code: "); Serial.println(code);
    return false;
  }
  return true;
}

bool chttpsSendRaw(const String& data) {
  // Sequence: issue SEND, wait for DOWNLOAD prompt, send payload, wait for final OK
  while (Modem.available()) Modem.read();
  Modem.print(String("AT+CHTTPSSEND=") + data.length() + ",10000\r\n");
  String dl;
  if (!atWaitFor("DOWNLOAD", dl, 7000)) { Serial.println("[CHTTPS] No DOWNLOAD prompt"); return false; }
  Modem.print(data);
  String ok;
  if (!atWaitFor("\r\nOK\r\n", ok, 15000)) { Serial.println("[CHTTPS] No OK after sending payload"); return false; }
  return true;
}

bool chttpsRecvAll(String& out, uint32_t maxWaitMs = 30000) {
  out = "";
  uint32_t start = millis();
  while (millis() - start < maxWaitMs) {
    // Query available size
    String q;
    bool ok = atSendAndGetResponse("AT+CHTTPSRECV?", q, 3000);
    if (!ok) {
      delay(150);
      continue;
    }
    // Expect "+CHTTPSRECV: <len>"
    int p = q.indexOf("+CHTTPSRECV:");
    int available = 0;
    if (p >= 0) {
      int nl = q.indexOf('\n', p);
      String line = nl > 0 ? q.substring(p, nl) : q.substring(p);
      int colon = line.indexOf(':');
      if (colon > 0) {
        String num = line.substring(colon + 1);
        num.trim();
        available = num.toInt();
      }
    }
    if (available <= 0) {
      // No data yet; small backoff
      delay(120);
      continue;
    }
    int toRead = available;
    if (toRead > 1460) toRead = 1460;
    String cmd = String("AT+CHTTPSRECV=") + toRead;
    if (!atSendAndWaitOK(cmd)) return false;
    String rd;
    if (!atWaitFor("+CHTTPSRECV:", rd, 8000)) break;
    int hdr = rd.indexOf("+CHTTPSRECV:");
    if (hdr < 0) break;
    int nl = rd.indexOf('\n', hdr);
    if (nl <= 0) break;
    int okPos = rd.lastIndexOf("\r\nOK\r\n");
    if (okPos > nl) {
      String chunk = rd.substring(nl + 1, okPos);
      out += chunk;
      if (chunk.length() < toRead) {
        // Probably end of data
        break;
      }
    } else {
      break;
    }
    // Continue until timeout or no more data
    delay(40);
  }
  return out.length() > 0;
}

bool chttpsClose() {
  return atSendAndWaitOK("AT+CHTTPSCLSE");
}

int parseHttpStatus(const String& raw) {
  // Try HTTP/1.1 first
  int p = raw.indexOf("HTTP/1.1 ");
  if (p >= 0 && p + 12 <= (int)raw.length()) {
    return raw.substring(p + 9, p + 12).toInt();
  }
  // Then HTTP/2 (Cloudflare can reply with this status line)
  p = raw.indexOf("HTTP/2 ");
  if (p >= 0 && p + 9 <= (int)raw.length()) {
    return raw.substring(p + 7, p + 10).toInt();
  }
  return -1;
}

bool chttpsGet(const String& host, const String& path, int& statusCode, String& body) {
  statusCode = -1; body = "";
  if (!chttpsStart()) return false;
  bool ok = chttpsOpen(host, 443);
  if (!ok) { chttpsStop(); return false; }
  String req = String("GET ") + path + " HTTP/1.1\r\n";
  req += String("Host: ") + host + "\r\n";
  req += "User-Agent: SIM7600/1.0\r\n";
  req += "Accept: */*\r\n";
  req += "Connection: close\r\n\r\n";
  if (!chttpsSendRaw(req)) { chttpsClose(); chttpsStop(); return false; }
  String raw;
  // Allow server some time to respond before polling
  delay(300);
  chttpsRecvAll(raw, 30000);
  chttpsClose();
  chttpsStop();
  if (raw.length() == 0) return false;
  // Log small snippet for debugging
  Serial.print("[CHTTPS] header snippet: "); Serial.println(raw.substring(0, 120));
  // Parse status line (support HTTP/1.1 and HTTP/2)
  statusCode = parseHttpStatus(raw);
  int sep = raw.indexOf("\r\n\r\n");
  if (sep > 0) body = raw.substring(sep + 4);
  Serial.print("[CHTTPS] status: "); Serial.println(statusCode);
  return statusCode > 0;
}

bool chttpsPost(const String& host, const String& path, const String& contentType, const String& payload, int& statusCode, String& body) {
  statusCode = -1; body = "";
  if (!chttpsStart()) return false;
  bool ok = chttpsOpen(host, 443);
  if (!ok) { chttpsStop(); return false; }
  String req = String("POST ") + path + " HTTP/1.1\r\n";
  req += String("Host: ") + host + "\r\n";
  req += String("Content-Type: ") + contentType + "\r\n";
  req += String("Content-Length: ") + payload.length() + "\r\n";
  req += "User-Agent: SIM7600/1.0\r\n";
  req += "Accept: */*\r\n";
  req += "Connection: close\r\n\r\n";
  req += payload;
  if (!chttpsSendRaw(req)) { chttpsClose(); chttpsStop(); return false; }
  String raw;
  delay(300);
  chttpsRecvAll(raw, 35000);
  chttpsClose();
  chttpsStop();
  if (raw.length() == 0) return false;
  Serial.print("[CHTTPS] header snippet: "); Serial.println(raw.substring(0, 120));
  statusCode = parseHttpStatus(raw);
  int sep = raw.indexOf("\r\n\r\n");
  if (sep > 0) body = raw.substring(sep + 4);
  Serial.print("[CHTTPS] status: "); Serial.println(statusCode);
  return statusCode > 0;
}

Servo barrier;
bool isOccupied = false;
uint32_t stateChangeAt = 0;
int lastRaw = HIGH;

// Health/Ping
bool serverReachable = false;
uint32_t lastHealthCheckAt = 0;
const uint32_t HEALTH_INTERVAL_MS = 60000; // alle 60s prüfen

void setBarrier(bool occupied) {
  int target = occupied ? CLOSED_ANGLE : OPEN_ANGLE;
  barrier.write(target);
  if (LED_PIN >= 0) digitalWrite(LED_PIN, occupied ? HIGH : LOW);
}

void announce() {
  Serial.print("Status: "); Serial.println(isOccupied ? "occupied" : "free");
}

bool modemReady = false;

// Versuche mehrere typische Baudraten, bis das Modem auf "AT" mit "OK" antwortet
bool initModemUARTAutoBaud() {
  const uint32_t BAUDS[] = {115200, 57600, 38400, 9600, 230400};
  const size_t N = sizeof(BAUDS) / sizeof(BAUDS[0]);
  for (size_t i = 0; i < N; ++i) {
    uint32_t b = BAUDS[i];
    Serial.print("[UART] Trying baud "); Serial.println(b);
    Modem.begin(b, SERIAL_8N1, MODEM_RX, MODEM_TX);
    delay(80);
    // Mehrfach probieren, da Modem gerade booten kann
    for (int attempt = 0; attempt < 3; ++attempt) {
      if (modem.testAT(1200)) {
        Serial.print("[UART] Modem responded at "); Serial.println(b);
        return true;
      }
      delay(120);
    }
  }
  Serial.println("[UART] No baud matched. Check wiring/power.");
  return false;
}

bool modemConnect() {
  if (modemReady) return true;

  Serial.println("[MODEM] Powering up and init...");
  delay(300);
  if (g_modemRecentlyRebooted) {
    Serial.println("[MODEM] Skipping restart (recent CFUN reboot)");
    g_modemRecentlyRebooted = false;
  } else {
    if (!modem.restart()) {
      Serial.println("[MODEM] restart failed (continuing)");
    }
  }
  String modemInfo = modem.getModemInfo();
  Serial.print("[MODEM] Info: "); Serial.println(modemInfo);

  // Ensure SIM ready and registered before TinyGSM waitForNetwork
  unlockSIMIfNeeded();
  waitForSIMReady(30000);
  waitForRegistration(45000);

  Serial.print("[MODEM] Waiting for network...");
  if (!modem.waitForNetwork(60000L)) {
    Serial.println(" fail");
    return false;
  }
  Serial.println(" OK");

  Serial.print("[MODEM] GPRS attach...");
  if (!modem.gprsConnect(APN, GPRS_USER, GPRS_PASS)) {
    Serial.println(" fail");
    return false;
  }
  Serial.println(" OK");
  modemReady = true;
  return true;
}

void sendStatusToBackend() {
  if (!modemConnect()) return;

  String path = String("/parking-spots/") + PARKING_SPOT_ID + "/status";
  String payload = String("{\"status\":\"") + (isOccupied ? "occupied" : "free") + "\"}";

  Serial.print("[HTTPS] POST "); Serial.println(path);
  int code = -1; String resp;
  bool ok = false;
  if (USE_HTTPS) {
    // Try legacy HTTP AT first, then fallback to CHTTPS (SNI-capable)
    ok = httpPostHTTPS(SERVER_HOST, path, "application/json", payload, code, resp);
    if (!ok || code <= 0) {
      Serial.println("[HTTPS] Falling back to CHTTPS POST...");
      ok = chttpsPost(SERVER_HOST, path, "application/json", payload, code, resp);
    }
  } else {
    HttpClient http(netClient, SERVER_HOST, SERVER_PORT);
    http.beginRequest(); http.post(path);
    http.sendHeader("Content-Type", "application/json");
    http.sendHeader("Content-Length", payload.length());
    http.beginBody(); http.print(payload); http.endRequest();
    code = http.responseStatusCode(); resp = http.responseBody(); ok = (code > 0);
  }
  Serial.print("[HTTP(S)] status: "); Serial.println(code);
  if (!ok) {
    Serial.print("[HTTP(S)] error resp: "); Serial.println(resp);
  }
}

bool pingHealth() {
  if (!modemConnect()) return false;
  // DNS check to confirm hostname resolves in the PDP context
  resolveHost(SERVER_HOST);
  Serial.println("[PING] GET /health");
  int statusCode = -1; String body;
  bool ok = false;
  if (USE_HTTPS) {
    // Try legacy HTTP AT first, then fallback to CHTTPS (SNI-capable)
    ok = httpGetHTTPS(SERVER_HOST, "/health", statusCode, body);
    if (!ok || statusCode <= 0) {
      Serial.println("[HTTPS] Falling back to CHTTPS GET...");
      ok = chttpsGet(SERVER_HOST, "/health", statusCode, body);
    }
  } else {
    HttpClient http(netClient, SERVER_HOST, SERVER_PORT);
    http.get("/health");
    statusCode = http.responseStatusCode();
    body = http.responseBody();
    ok = (statusCode > 0);
  }
  serverReachable = (statusCode == 200);
  Serial.print("[PING] status: "); Serial.println(statusCode);
  if (serverReachable) {
    Serial.print("[PING] body: "); Serial.println(body);
  }
  lastHealthCheckAt = millis();
  return serverReachable;
}

void updateStatusIfStable(int raw) {
  uint32_t now = millis();
  if (raw != lastRaw) {
    lastRaw = raw;
    stateChangeAt = now;
    return;
  }

  if (raw == LOW) {
    if (!isOccupied && (now - stateChangeAt >= OCCUPIED_CONFIRM_MS)) {
      isOccupied = true;
      setBarrier(isOccupied);
      announce();
      sendStatusToBackend();
    }
  } else {
    if (isOccupied && (now - stateChangeAt >= FREE_CONFIRM_MS)) {
      isOccupied = false;
      setBarrier(isOccupied);
      announce();
      sendStatusToBackend();
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("Smart Parking (SIM7600) start...");

  if (LED_PIN >= 0) { pinMode(LED_PIN, OUTPUT); digitalWrite(LED_PIN, LOW); }
  pinMode(HALL_PIN, INPUT_PULLUP);
  lastRaw = digitalRead(HALL_PIN);
  stateChangeAt = millis();

  barrier.setPeriodHertz(50);
  barrier.attach(SERVO_PIN, 500, 2500);
  barrier.write(CLOSED_ANGLE);
  delay(300);
  isOccupied = (HALL_LOW_IS_OCCUPIED ? (lastRaw == LOW) : (lastRaw == HIGH));
  setBarrier(isOccupied);
  announce();

  // UART für Modem initialisieren (Auto-Baud, falls Modem noch nicht auf 115200 ist)
  if (!initModemUARTAutoBaud()) {
    Serial.println("[ERR] Could not sync with modem over UART.");
  }
  // Persist UART settings and disable echo for cleaner logs; then resync
  persistModemSettings();
  // Basic AT health checks for visibility
  runBasicATHealth();
  modemConnect();
// HTTPS-Notiz: Für SIM7600 ist TinyGsmClientSecure nicht verfügbar.
// Wenn HTTPS zwingend ist, bitte auf SIM7600-HTTPS-AT-Kommandos wechseln.
  // Health-Check vor dem ersten Senden
  pingHealth();
  if (serverReachable) {
    sendStatusToBackend();
  }
}

void loop() {
  int raw = digitalRead(HALL_PIN);
  int logical = raw;
  if (!HALL_LOW_IS_OCCUPIED) logical = (raw == LOW) ? HIGH : LOW;
  updateStatusIfStable(logical);
  // periodischer Health-Check
  if (millis() - lastHealthCheckAt >= HEALTH_INTERVAL_MS) {
    pingHealth();
  }
  delay(10);
}
