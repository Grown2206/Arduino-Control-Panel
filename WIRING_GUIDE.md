# 🔌 Verkabelungs-Guide - Arduino Control Panel

## 📋 Benötigte Bauteile

### Hardware
- ✅ Arduino Uno/Nano
- ✅ USB-Kabel (A zu B für Uno, A zu Mini-B für Nano)
- ✅ Breadboard
- ✅ Jumperkabel (M-M, M-F)

### Sensoren (optional, je nach Bedarf)
- 🌡️ DHT11 oder DHT22 (Temperatur/Luftfeuchtigkeit)
- 📏 HC-SR04 (Ultraschall-Distanzsensor)
- 💡 LDR + 10kΩ Widerstand (Lichtsensor)
- 📳 SW-420 (Vibrationssensor)

---

## 🔌 Schaltplan - Komplettaufbau

```
┌─────────────────────────────────────────────────────────────┐
│                    ARDUINO UNO                              │
│                                                             │
│  D2 ────────────── SW-420 Vibrationssensor                 │
│  D3 ────────────── DHT11/DHT22 (DATA Pin)                  │
│  D9 ────────────── HC-SR04 (TRIGGER)                       │
│  D10 ───────────── HC-SR04 (ECHO)                          │
│  D13 ───────────── LED (Onboard, Test)                     │
│                                                             │
│  A0 ────────────── LDR Spannungsteiler                     │
│                                                             │
│  5V ────┬────────── Alle Sensor VCC                        │
│  GND ───┴────────── Alle Sensor GND                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌡️ DHT11/DHT22 Verkabelung

### Pinout DHT11/DHT22

```
   ┌─────────┐
   │ DHT11   │
   │  ┌───┐  │
   │  │ ▓ │  │  Front-Ansicht
   │  └───┘  │
   └─┬─┬─┬─┬─┘
     1 2 3 4
```

| Pin | Name | Arduino |
|-----|------|---------|
| 1 | VCC | 5V |
| 2 | DATA | D3 |
| 3 | NC | - |
| 4 | GND | GND |

### Breadboard-Schaltung

```
     5V ────────────── Pin 1 (VCC)

     D3 ────┬──────── Pin 2 (DATA)
            │
         [4.7kΩ]  ← Pull-up Widerstand (oft integriert)
            │
     5V ────┘

     GND ───────────── Pin 4 (GND)
```

**Wichtig:**
- ✅ Manche DHT-Module haben den Pull-up bereits integriert
- ✅ 4.7kΩ oder 10kΩ Widerstand zwischen DATA und VCC
- ⚠️ DHT22 ist genauer, aber teurer als DHT11

---

## 📏 HC-SR04 Ultraschallsensor

### Pinout HC-SR04

```
   ┌───────────┐
   │  ┃    ┃   │
   │  ┃ ░░ ┃   │  ← Ultraschall-Sender/Empfänger
   │  ┃    ┃   │
   └─┬──┬──┬──┬┘
     1  2  3  4
    VCC T  E GND
```

| Pin | Name | Arduino |
|-----|------|---------|
| VCC | Power | 5V |
| TRIG | Trigger | D9 |
| ECHO | Echo | D10 |
| GND | Ground | GND |

### Verkabelung

```
Arduino          HC-SR04
   5V  ────────── VCC
   D9  ────────── TRIG
   D10 ────────── ECHO
   GND ────────── GND
```

**Messbereich:** 2 cm - 4 m
**Genauigkeit:** ±3 mm

**Hinweis:** Bei 3.3V-Arduinos (z.B. Due) benötigt ECHO einen Spannungsteiler!

```
ECHO ───┬─── D10 (3.3V Arduino)
        │
      [1kΩ]
        │
      [2kΩ]
        │
       GND
```

---

## 💡 LDR Lichtsensor

### Schaltung (Spannungsteiler)

```
    5V ───┬
          │
        [LDR]  ← Fotowiderstand (variabel: 1kΩ - 1MΩ)
          │
          ├────── A0 (Messung)
          │
       [10kΩ]  ← Fester Widerstand
          │
         GND
```

### Breadboard-Layout

```
       5V Rail
         │
         LDR
         │
    ┌────┼────┐
    │    A0   │  Arduino Analog Pin
    └─────────┘
         │
       10kΩ
         │
       GND Rail
```

**Funktionsweise:**
- **Viel Licht** → LDR-Widerstand niedrig → A0 ≈ 0-300
- **Wenig Licht** → LDR-Widerstand hoch → A0 ≈ 700-1023

**Alternative Schaltung (invertiert):**
```
    5V ───┬
          │
       [10kΩ]
          │
          ├────── A0
          │
        [LDR]
          │
         GND
```
→ Hier bedeutet hoher Wert = hell

---

## 📳 SW-420 Vibrationssensor

### Pinout SW-420

```
   ┌────────────┐
   │   SW-420   │
   │  ┌──────┐  │
   │  │ POT  │  │  ← Empfindlichkeits-Regler
   │  └──────┘  │
   │   ●  ●  ●  │
   │  VCC D GND │
   └────────────┘
```

| Pin | Name | Arduino |
|-----|------|---------|
| VCC | Power | 5V |
| D/DO | Digital Out | D2 |
| GND | Ground | GND |

### Verkabelung

```
Arduino          SW-420
   5V  ────────── VCC
   D2  ────────── D/DO
   GND ────────── GND
```

**Einstellung:**
1. Drehe Potentiometer (POT) im Uhrzeigersinn = empfindlicher
2. LED auf Modul leuchtet bei Vibration
3. Ausgabe: HIGH = Vibration erkannt

---

## 🔋 Stromversorgung

### Option 1: USB (empfohlen für Entwicklung)
```
PC/Laptop [USB] ────── Arduino
```
- ✅ Gleichzeitig Stromversorgung + Daten
- ⚠️ Begrenzt auf ~500mA

### Option 2: Externes Netzteil
```
9V Netzteil ────── DC Barrel Jack (Arduino)
```
- ✅ Bis zu 1A möglich
- ✅ Unabhängig vom PC
- ⚠️ Arduino regelt auf 5V runter (ineffizient)

### Option 3: Batterie
```
9V Batterie ────── DC Barrel Jack
```
- ✅ Mobil
- ⚠️ Batterie hält nur ~2-3 Stunden

**Stromverbrauch (geschätzt):**
| Komponente | Strom |
|------------|-------|
| Arduino Uno | ~50mA |
| DHT11 | 2.5mA |
| HC-SR04 | 15mA |
| LDR Circuit | 0.5mA |
| SW-420 | 3mA |
| **Gesamt** | ~71mA |

→ USB reicht aus!

---

## 🧪 Test-Checkliste

### Vor dem Hochladen

- [ ] Alle VCC an 5V?
- [ ] Alle GND an GND?
- [ ] Keine Kurzschlüsse?
- [ ] Sensoren fest verkabelt?
- [ ] USB-Kabel angeschlossen?

### Nach dem Hochladen

1. **Serial Monitor öffnen** (115200 Baud)
2. **Startup-Nachricht?**
   ```json
   {"type":"status","message":"Arduino Control Panel v4.0 bereit"}
   ```
3. **Test DHT11:**
   ```json
   {"id":"test1","command":"read_sensor","sensor":"B24_TEMP_HUMIDITY"}
   ```
   Erwarte: Temperatur + Luftfeuchtigkeit

4. **Test HC-SR04:**
   ```json
   {"id":"test2","command":"read_sensor","sensor":"HC_SR04"}
   ```
   Erwarte: Distanz in cm

5. **Test LDR:**
   ```json
   {"id":"test3","command":"read_sensor","sensor":"LDR"}
   ```
   Erwarte: Wert 0-1023

6. **Test LED (Onboard D13):**
   ```json
   {"id":"test4","command":"pin_mode","pin":"D13","mode":"OUTPUT"}
   {"id":"test5","command":"digital_write","pin":"D13","value":1}
   ```
   LED sollte leuchten!

---

## 🐛 Fehlersuche

### Sensor gibt keine Werte

**DHT11/DHT22:**
1. ✅ Pin 1 = 5V, Pin 4 = GND?
2. ✅ DATA-Pin richtig (Standard D3)?
3. ✅ Pull-up Widerstand vorhanden?
4. ⏰ Warte 2 Sekunden nach Einschalten

**HC-SR04:**
1. ✅ VCC = 5V, GND = GND?
2. ✅ Nichts blockiert die Sensoren?
3. ✅ TRIG/ECHO nicht vertauscht?
4. 📏 Objekt in 2cm-4m Entfernung?

**LDR:**
1. ✅ Spannungsteiler korrekt?
2. ✅ 10kΩ Widerstand verwendet?
3. 💡 Lichtquelle vorhanden für Test?

---

## 📸 Beispiel-Aufbau

### Minimal-Setup (nur DHT11)

```
  Breadboard:
  ┌─────────────────┐
  │  5V Rail        │
  │   │             │
  │   └─┬─ DHT VCC  │
  │     │           │
  │   ┌─┴─┐         │
  │   │DHT│         │
  │   └─┬─┘         │
  │     │           │
  │     ├─ D3 ──────┼──── Arduino D3
  │     │           │
  │     └─ GND      │
  │  GND Rail       │
  └─────────────────┘
```

### Komplett-Setup (alle Sensoren)

```
  Breadboard:
  ┌──────────────────────────────────┐
  │  5V Rail ───┬─── DHT VCC         │
  │             ├─── HC-SR04 VCC     │
  │             ├─── SW-420 VCC      │
  │             └─── LDR (top)       │
  │                                  │
  │  DHT DATA ────────────── D3      │
  │  HC-SR04 TRIG ───────── D9       │
  │  HC-SR04 ECHO ───────── D10      │
  │  SW-420 DATA ────────── D2       │
  │  LDR Middle ─────────── A0       │
  │                                  │
  │  GND Rail ───┬─── DHT GND        │
  │              ├─── HC-SR04 GND    │
  │              ├─── SW-420 GND     │
  │              └─── LDR (via 10kΩ) │
  └──────────────────────────────────┘
```

---

## 🎯 Quick-Start

**5-Minuten-Setup:**

1. **Verbinde Arduino** via USB
2. **Öffne Arduino IDE** → Lade `arduino_control_panel_v4.ino`
3. **Upload** → Warte auf "Done uploading"
4. **Öffne Python Control Panel** → Wähle Port → Connect
5. **Fertig!** 🎉

---

## 📚 Weiterführende Links

- [Arduino Uno Pinout](https://docs.arduino.cc/hardware/uno-rev3)
- [DHT11 Datasheet](https://www.mouser.com/datasheet/2/758/DHT11-Technical-Data-Sheet-Translated-Version-1143054.pdf)
- [HC-SR04 Tutorial](https://randomnerdtutorials.com/complete-guide-for-ultrasonic-sensor-hc-sr04/)
- [LDR Guide](https://learn.adafruit.com/photocells)

---

**Viel Erfolg beim Verkabeln!** 🔧
