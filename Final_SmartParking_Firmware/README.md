# Final SmartParking Firmware (ESP32-S3 + SIM7600)

This folder contains a single-file Arduino sketch ready to flash: `Final_SmartParking_Firmware.ino`.

## What it does
- Controls your barrier via a hobby servo on GPIO 21 (default; changeable at runtime)
- Talks to your backend over LTE (SIM7600) using HTTPS/TLS (SNI enabled)
- Reads ultrasonic + hall sensor for occupancy, sends periodic heartbeats
- Includes a serial REPL for quick tests and field diagnostics

## Hardware pinout
- Servo signal: GPIO 21
  - Power servo from Pololu REG26A 5V; GND shared with ESP32-S3.
- SIM7600: RX=27 (ESP32 RX pin), TX=26 (ESP32 TX pin), PWRKEY=19
- Hall sensor (A3144E): GPIO 32 (active LOW, use internal pull-up)
- Ultrasonic: TRIG=23, ECHO=22
- Emergency stop: GPIO 16 (active LOW)
- Relays (if ever used instead of servo): UP=25, DOWN=17
- Status LED: GPIO 2

## Build requirements
- Arduino IDE (or Arduino CLI) with ESP32 boards installed (ESP32 Arduino core 2.x or 3.x)
- Board: "ESP32S3 Dev Module" (Tools -> Board)
- Optional PSRAM: Disabled (or as your board supports)
- Libraries:
  - ArduinoJson by Benoit Blanchon (v6+)
  - Optional: ESP32Servo by Kevin Harrington (auto-used if installed). If not installed, the built-in LEDC PWM is used.

## Flashing
1. Open `Final_SmartParking_Firmware.ino` in the Arduino IDE (the folder name matches the sketch name).
2. Select Tools -> Board -> ESP32 -> ESP32S3 Dev Module.
3. Select the correct Port (USB).
4. Click Upload.

## First USB-only test (no Pololu, safe current)
- Open Serial Monitor at 115200 baud.
- Type:
  - `modem off` (skips SIM/LTE bring-up)
  - `servo gentle on` (soft micro-stepping to limit current)
  - `status`
  - `sweep` (moves servo between 1000us-2000us)
- When ready for field use: `servo gentle off`, then `modem on`.

## Useful REPL commands
- `status` — prints barrier, servo config, hall, modem state.
- `up` / `down` / `mid` / `sweep`
- `servo up=2000 down=1000 delay=900 [persist=1]` — tune and optionally save.
- `servo pin=21 [test]` — reattach servo to another GPIO at runtime; optional quick test.
- `servo gentle on|off` — enable soft stepping for bench tests.
- `modem off|on` — disable/enable LTE logic (helpful on USB power).
- `at <CMD>` / `sim pulse|invert|test` — modem diagnostics.

## Backend
- API base is set to `https://api.gashis.ch/api` in the sketch.
- Device ID: `PARK_DEVICE_001` (change in the code if needed).

## Notes
- Ensure common GND between ESP32-S3, SIM7600, and Pololu 5V regulator.
- Add bulk capacitors near servo (470–1000 µF) and modem (1000–2200 µF) for stability.
- If you see 403/404 from the backend, test the endpoints directly on the server and verify the Nginx routing to FastAPI.
