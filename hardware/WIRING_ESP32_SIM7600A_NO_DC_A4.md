# Verkabelung – Variante A ohne DC‑Stecker (A4)

Dieses Blatt ergänzt die No‑DC‑Anleitung. Drucke das SVG auf A4 (100 %) und nutze es als Referenz beim Verdrahten.

- Datei: `WIRING_ESP32_SIM7600A_NO_DC_A4.svg`
- Empfohlene Druckeinstellung: "Tatsächliche Größe" / 100 %, Querformat wird automatisch erkannt.
- Farblegende: Rot=+5 V, Schwarz=GND, Blau=Signale (UART/3.3 V), Orange=Servo, Grün=Hall OUT.
- Hinweise:
  - Gemeinsame Masse zwingend. Servo niemals an 3.3 V.
  - Leitungen kurz halten; Querschnitt 0.5–1.0 mm², Hauptzufuhr 0.75–1.0 mm².
  - WAGO 221: Stripplänge ~11 mm; Deckel vollständig schließen, danach Zugprobe.
  - Optionalpuffer: 1000 µF (HAT) und 330–470 µF (Servo) + je 100 nF Keramik.

Siehe Schritt‑für‑Schritt: `hardware/ASSEMBLY_QUICKSTART_VAR_A_NO_DC.md`.
