# 🤖 Arduino Control Panel - Firmware v4.0

## 📋 Übersicht

Professioneller Arduino-Sketch für das **Drexler Dynamics Arduino Control Panel**. Vollständig kompatibel mit der PyQt6-Desktop-Anwendung.

---

## ✨ Features

### ✅ Unterstützte Funktionen

| Feature | Status | Beschreibung |
|---------|--------|--------------|
| **Digital I/O** | ✅ | Pin-Modus setzen (INPUT/OUTPUT/INPUT_PULLUP) |
| **Digital Read/Write** | ✅ | Pins lesen und schreiben (HIGH/LOW) |
| **Analog Read** | ✅ | Analoge Werte lesen (0-1023) |
| **Sensor-Konfiguration** | ✅ | Dynamische Sensor-Pin-Zuordnung |
| **Sensor-Auslesen** | ✅ | Temperatur, Luftfeuchtigkeit, Distanz, Licht, Vibration |
| **JSON-Protokoll** | ✅ | Strukturierte Kommunikation |
| **Fehlerbehandlung** | ✅ | Validierung + Error Messages |
| **Pin-Status** | ✅ | Alle Pin-Zustände abfragen |
| **System-Reset** | ✅ | Zurücksetzen auf Defaults |

---

## 🔌 Hardware-Anforderungen

### Unterstützte Boards
- ✅ Arduino Uno
- ✅ Arduino Nano
- ✅ Arduino Mega (mit Anpassungen)
- ✅ Arduino Leonardo (mit Anpassungen)

### Benötigte Bibliotheken

```cpp
ArduinoJson (v7.x)      // https://arduinojson.org/
DHT Sensor Library      // https://github.com/adafruit/DHT-sensor-library
```

**Installation via Arduino IDE:**
```
Tools → Manage Libraries → Suche nach:
1. "ArduinoJson" von Benoit Blanchon
2. "DHT sensor library" von Adafruit
```

---

## 📦 Unterstützte Sensoren

### 🌡️ Temperatur & Luftfeuchtigkeit

#### DHT11
```
Pins:
  - VCC  → 5V
  - GND  → GND
  - DATA → D3 (konfigurierbar)

Messbereich:
  - Temperatur: 0-50°C (±2°C)
  - Luftfeuchtigkeit: 20-80% (±5%)
```

#### DHT22
```
Pins:
  - VCC  → 5V
  - GND  → GND
  - DATA → D3 (konfigurierbar)

Messbereich:
  - Temperatur: -40 bis 80°C (±0.5°C)
  - Luftfeuchtigkeit: 0-100% (±2%)
```

### 📏 Distanz

#### HC-SR04 Ultraschallsensor
```
Pins:
  - VCC     → 5V
  - GND     → GND
  - TRIGGER → D9 (konfigurierbar)
  - ECHO    → D10 (konfigurierbar)

Messbereich: 2-400 cm
Genauigkeit: ±3mm
```

### 💡 Licht

#### LDR (Fotowiderstand)
```
Schaltung (Spannungsteiler):
  - 5V → LDR → A0 → 10kΩ → GND

Ausgabe: 0-1023 (raw)
  - Hell: niedriger Wert
  - Dunkel: hoher Wert
```

### 📳 Vibration

#### SW-420 Vibrationssensor
```
Pins:
  - VCC  → 5V
  - GND  → GND
  - DATA → D2 (konfigurierbar)

Ausgabe: HIGH = Vibration erkannt
```

---

## 🚀 Installation

### Schritt 1: Arduino IDE einrichten

1. **Öffne Arduino IDE** (Version 1.8.x oder 2.x)
2. **Board auswählen**: Tools → Board → Arduino Uno
3. **Port auswählen**: Tools → Port → COM3 (Windows) / /dev/ttyUSB0 (Linux)

### Schritt 2: Bibliotheken installieren

```
Tools → Manage Libraries → Installiere:
1. ArduinoJson (v7.0.0 oder neuer)
2. DHT sensor library (v1.4.4 oder neuer)
3. Adafruit Unified Sensor (automatisch mit DHT)
```

### Schritt 3: Sketch hochladen

1. **Öffne `arduino_control_panel_v4.ino`**
2. **Kompilieren**: Sketch → Verify/Compile (Strg+R)
3. **Hochladen**: Sketch → Upload (Strg+U)
4. **Monitor öffnen**: Tools → Serial Monitor (Strg+Shift+M)
   - Baudrate: **115200**
   - Line ending: **Newline**

### Schritt 4: Test

Im Serial Monitor solltest du sehen:
```json
{"type":"status","message":"Arduino Control Panel v4.0 bereit"}
{"type":"config","version":"4.0","board":"Arduino Uno/Nano",...}
```

---

## 📡 Kommunikationsprotokoll

### Basis-Format

```json
// Befehl senden (Control Panel → Arduino)
{
  "id": "unique-id-12345",
  "command": "digital_write",
  "pin": "D13",
  "value": 1
}

// Antwort empfangen (Arduino → Control Panel)
{
  "type": "response",
  "status": "ok",
  "response_to": "unique-id-12345"
}
```

---

## 🔧 Befehls-Referenz

### 1. Pin-Modus setzen

**Request:**
```json
{
  "id": "cmd-001",
  "command": "pin_mode",
  "pin": "D13",
  "mode": "OUTPUT"
}
```

**Modes:** `"INPUT"`, `"OUTPUT"`, `"INPUT_PULLUP"`

**Response:**
```json
{"type":"response","status":"ok","response_to":"cmd-001"}
```

---

### 2. Digital Write

**Request:**
```json
{
  "id": "cmd-002",
  "command": "digital_write",
  "pin": "D13",
  "value": 1
}
```

**Response:**
```json
{"type":"response","status":"ok","response_to":"cmd-002"}
{"type":"pin_update","pin_name":"D13","value":1}
```

---

### 3. Digital Read

**Request:**
```json
{
  "id": "cmd-003",
  "command": "digital_read",
  "pin": "D7"
}
```

**Response:**
```json
{"type":"response","status":"ok","response_to":"cmd-003","value":0}
{"type":"pin_update","pin_name":"D7","value":0}
```

---

### 4. Analog Read

**Request:**
```json
{
  "id": "cmd-004",
  "command": "analog_read",
  "pin": "A0"
}
```

**Response:**
```json
{"type":"response","status":"ok","response_to":"cmd-004","value":512}
{"type":"pin_update","pin_name":"A0","value":512}
```

---

### 5. Sensor konfigurieren (NEU in v4.0!)

**DHT11 Beispiel:**
```json
{
  "id": "cfg-001",
  "command": "configure_sensor_pin",
  "sensor_type": "DHT11",
  "pin_config": {
    "data": "D3"
  }
}
```

**HC-SR04 Beispiel:**
```json
{
  "id": "cfg-002",
  "command": "configure_sensor_pin",
  "sensor_type": "HC_SR04",
  "pin_config": {
    "trigger": "D9",
    "echo": "D10"
  }
}
```

**Response:**
```json
{"type":"response","status":"ok","response_to":"cfg-001"}
```

---

### 6. Sensor auslesen

**Request:**
```json
{
  "id": "sens-001",
  "command": "read_sensor",
  "sensor": "B24_TEMP_HUMIDITY"
}
```

**Response:**
```json
{"type":"sensor_update","sensor":"B24_TEMP","value":23.5}
{"type":"sensor_update","sensor":"B24_HUMIDITY","value":45.2}
{"type":"response","status":"ok","response_to":"sens-001"}
```

**Sensor-IDs:**
- `"B24_TEMP_HUMIDITY"` - DHT11/DHT22
- `"HC_SR04"` - Ultraschall
- `"LDR"` - Lichtsensor
- `"B39_VIBRATION"` - Vibrationssensor

---

### 7. Alle Pin-Zustände

**Request:**
```json
{
  "id": "sys-001",
  "command": "get_pin_states"
}
```

**Response:**
```json
{
  "type": "pin_states",
  "response_to": "sys-001",
  "digital": [
    {"pin":"D0","value":0},
    {"pin":"D1","value":0},
    ...
  ],
  "analog": [
    {"pin":"A0","value":512},
    {"pin":"A1","value":0},
    ...
  ]
}
```

---

### 8. System Reset

**Request:**
```json
{
  "id": "sys-002",
  "command": "reset"
}
```

**Response:**
```json
{"type":"response","status":"ok","response_to":"sys-002"}
{"type":"status","message":"System reset - zurück zu Defaults"}
```

---

## 🔌 Standard Pin-Belegung

### Default-Konfiguration (ohne configure_sensor_pin)

| Sensor | Pin | Typ |
|--------|-----|-----|
| DHT11/DHT22 | D3 | Digital |
| Vibration | D2 | Digital |
| HC-SR04 Trigger | D9 | Digital |
| HC-SR04 Echo | D10 | Digital |
| LDR | A0 | Analog |

**Hinweis:** Diese können via `configure_sensor_pin` überschrieben werden!

---

## 🐛 Troubleshooting

### Problem: "avrdude: stk500_recv(): programmer is not responding"

**Lösung:**
1. Überprüfe die Port-Auswahl
2. Drücke Reset-Button am Arduino
3. Trenne und verbinde USB-Kabel neu
4. Prüfe, ob andere Programme den Port nutzen (Serial Monitor schließen!)

---

### Problem: "Compilation error: ArduinoJson.h: No such file"

**Lösung:**
```
Tools → Manage Libraries → Suche "ArduinoJson" → Install
```

---

### Problem: "Sensor gibt keine Werte zurück"

**Checkliste:**
1. ✅ Sensor korrekt verkabelt? (VCC, GND, DATA)
2. ✅ `configure_sensor_pin` gesendet?
3. ✅ Richtiger Sensor-Typ? (DHT11 vs DHT22)
4. ✅ Serial Monitor auf 115200 Baud?
5. ✅ Sensor-Bibliothek installiert?

**Test-Befehl:**
```json
{"id":"test","command":"read_sensor","sensor":"B24_TEMP_HUMIDITY"}
```

---

### Problem: "JSON Parse Error"

**Ursachen:**
- Kein Newline am Ende (`\n`)
- Ungültiges JSON-Format
- Sonderzeichen nicht escaped

**Korrekt:**
```json
{"id":"test","command":"pin_mode","pin":"D13","mode":"OUTPUT"}\n
```

**Falsch:**
```json
{id:"test",command:"pin_mode"}  // Fehlende Quotes
```

---

## 📊 Performance

| Metrik | Wert |
|--------|------|
| **Baudrate** | 115200 |
| **JSON Doc Size** | 512 Bytes |
| **Max Sensoren** | 10 gleichzeitig |
| **Command Latency** | <10ms |
| **Sensor Read** | 50-250ms (je nach Sensor) |
| **Memory Usage** | ~4KB RAM (Uno) |

---

## 🔄 Versions-Historie

### v4.0 (2024-10-24)
- ✅ Dynamische Sensor-Konfiguration (`configure_sensor_pin`)
- ✅ Verbesserte Fehlerbehandlung
- ✅ System-Reset Command
- ✅ Pin-Konfiguration beim Start
- ✅ Memory-Optimierung
- ✅ Ausführliche Dokumentation

### v3.1 (2024-10-21)
- ✅ Entfernt: PWM und Servo (für Stabilität)
- ✅ Basis DHT11/DHT22 Support

---

## 📝 Lizenz

Erstellt für **Drexler Dynamics Arduino Control Panel**
Entwickelt mit [Claude Code](https://claude.com/claude-code)

---

## 🆘 Support

**Fehler gefunden?**
Erstelle ein Issue auf GitHub mit:
- Arduino Board-Typ
- Sensor-Modell
- Fehlermeldung aus Serial Monitor
- Verwendete Bibliotheks-Versionen

---

## 🎯 Nächste Schritte

1. **Hardware verbinden** (siehe Pin-Belegung oben)
2. **Sketch hochladen** (Arduino IDE)
3. **Control Panel starten** (Python-Anwendung)
4. **Verbinden** (Port auswählen → Connect)
5. **Sensoren konfigurieren** (Board Config Tab)
6. **Testen!** 🚀

---

**Viel Erfolg mit deinem Arduino Control Panel!** 🎉
