# MMC5603 (Adafruit Triple-axis Magnetometer) — Wiring & Notes

This document describes wiring, mounting and a short calibration/test procedure for the Adafruit MMC5603 (STEMMA QT / Qwiic) when used as a parking-occupancy sensor.

Hardware wiring (ESP32 example)
- VIN -> 3.3V (do NOT use 5V)
- GND -> GND
- SDA -> GPIO32 (user-provided)
- SCL -> GPIO33 (user-provided)

Notes
- The MMC5603 is I2C. If your board uses different pins for I2C, adjust the firmware `Wire.begin(SDA_pin, SCL_pin);` accordingly.
- Avoid pins that are used for SPI flash (6..11), UART0 (1/3) or boot strapping pins (0,2,15) when choosing SCL/SDA.
- Keep the sensor and magnet orientation fixed. Small changes in distance/orientation impact readings strongly.

Mechanical placement
- Mount the magnet on the inner side of the parking-bügel (or car contacting surface) so the distance to the MMC5603 is consistent when parked.
- Use non-conductive spacers to avoid shorting.
- Minimize vibration and use foam/damping if necessary.

Firmware & Calibration (recommended)
1. Power up the device in an empty space (no car present).
2. Run the built-in calibration routine (firmware example performs ~10s by default). It calculates baseline magnitude and sigma.
3. Record the reported baseline and sigma values in logs (serial output).
4. Test by bringing a car (or magnet) into position and removing it several times.

Suggested starting parameters (can be tuned per site)
- Sampling: 25 Hz
- Moving average window: 10 samples
- Calibration: 10–15 seconds
- T_on = max(10 µT, baseline*0.05, 3*sigma)
- T_off = T_on * 0.6
- Debounce = 2500 ms (require stable reading for 2.5s before switching state)

Testing
- Upload `firmware/esp32/mmc5603_example.ino` to your ESP32 (fill WiFi credentials first if you want backend POSTs)
- Open serial monitor (115200 baud). Observe baseline printed after calibration.
- Move magnet/car into place repeatedly to verify state flips with low false-positives.

Troubleshooting
- Too many false positives: increase T_on or increase debounce/window size.
- Missed events: reduce debounce or lower T_on slightly.
- High vibration: add mechanical damping, increase window size and debounce.

Next steps
- After field tuning, commit final thresholds into device config or make them configurable via OTA or a simple HTTP endpoint on the device.
