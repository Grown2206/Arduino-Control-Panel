# 🌐 Arduino Control Panel REST API

## Übersicht

Das Arduino Control Panel bietet eine vollständige REST API mit Swagger-Dokumentation für externe Steuerung und Integration.

## 🚀 Schnellstart

### 1. Server starten

Der REST API Server startet automatisch mit dem Arduino Control Panel auf Port **5000**.

### 2. Swagger Dokumentation

Öffne im Browser: **http://localhost:5000/api/docs**

Hier findest du die interaktive API-Dokumentation mit allen Endpoints und Beispielen.

### 3. API Key

Für schreibende Operationen (POST, PUT, DELETE) wird ein API Key benötigt.

**Default API Key:** `default-api-key-change-me`

**Header:** `X-API-Key: dein-api-key`

## 📚 API Endpoints

### System

#### GET /api/system/status
System-Status abrufen
```json
{
  "status": "online",
  "version": "1.0.0",
  "connected": true,
  "timestamp": "2025-10-24T12:30:00"
}
```

#### GET /api/system/info
Detaillierte System-Informationen
```json
{
  "application": "Arduino Control Panel",
  "version": "1.0.0",
  "features": {
    "analytics": true,
    "hardware_profiles": true,
    "calibration": true
  },
  "statistics": {
    "sequences": 5,
    "profiles": 3
  }
}
```

---

### Pins

#### GET /api/pins/
Liste aller Pins
```json
{
  "pins": {
    "D13": {
      "name": "D13",
      "mode": "OUTPUT",
      "value": 1
    },
    "A0": {
      "name": "A0",
      "mode": "INPUT",
      "value": 512
    }
  }
}
```

#### GET /api/pins/{pin_name}
Pin-Status abrufen
```bash
curl http://localhost:5000/api/pins/D13
```

#### POST /api/pins/{pin_name}
Pin-Wert setzen (benötigt API Key)
```bash
curl -X POST http://localhost:5000/api/pins/D13 \
  -H "X-API-Key: default-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"pin": "D13", "value": 1}'
```

---

### Sensoren

#### GET /api/sensors/
Liste aller Sensoren
```json
{
  "sensors": {
    "B24_TEMP": {
      "name": "Temperatur (B24)",
      "value": 23.5,
      "unit": "°C",
      "min": 20.1,
      "max": 25.8
    },
    "B24_HUMIDITY": {
      "name": "Luftfeuchtigkeit (B24)",
      "value": 55.2,
      "unit": "%",
      "min": 50.0,
      "max": 60.5
    }
  }
}
```

#### GET /api/sensors/{sensor_id}
Sensor-Daten abrufen
```bash
curl http://localhost:5000/api/sensors/B24_TEMP
```

---

### Sequenzen

#### GET /api/sequences/
Liste aller Sequenzen
```json
{
  "sequences": {
    "seq_1": {
      "id": "seq_1",
      "name": "LED Blink Test",
      "cycles": 10,
      "steps": 4,
      "favorite": false
    }
  }
}
```

#### GET /api/sequences/{seq_id}
Sequenz-Details abrufen

#### POST /api/sequences/{seq_id}/start
Sequenz starten (benötigt API Key)
```bash
curl -X POST http://localhost:5000/api/sequences/seq_1/start \
  -H "X-API-Key: default-api-key-change-me"
```

---

### Archiv

#### GET /api/archive/
Liste aller Test-Läufe
```json
{
  "runs": [
    {
      "id": 1,
      "name": "Test #1",
      "sequence": "LED Blink",
      "start_time": "2025-10-24T12:00:00",
      "duration": 125.5,
      "cycles": 10,
      "status": "Abgeschlossen"
    }
  ]
}
```

---

### Kalibrierung

#### GET /api/calibration/
Liste aller Kalibrierungen
```json
{
  "calibrations": {
    "B24_TEMP": {
      "sensor_id": "B24_TEMP",
      "type": "two_point",
      "quality": 0.998,
      "active": true,
      "created": "2025-10-24T10:30:00"
    }
  }
}
```

---

## 🔌 WebSocket Live-Daten

### Verbindung herstellen

```javascript
// JavaScript Beispiel
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected to Arduino Control Panel WebSocket');

  // Abonniere Sensor-Daten
  socket.emit('subscribe', { type: 'sensors' });
});

// Empfange Sensor-Daten
socket.on('sensor_data', (data) => {
  console.log('Sensor Update:', data);
});

// Empfange Pin-Updates
socket.on('pin_update', (data) => {
  console.log('Pin Update:', data);
});
```

### Python Beispiel

```python
import socketio

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected to Arduino Control Panel')
    sio.emit('subscribe', {'type': 'sensors'})

@sio.on('sensor_data')
def on_sensor_data(data):
    print(f"Sensor: {data}")

@sio.on('pin_update')
def on_pin_update(data):
    print(f"Pin: {data}")

sio.connect('http://localhost:5000')
sio.wait()
```

---

## 🔒 API Keys verwalten

API Keys werden in `api_keys.json` gespeichert:

```json
{
  "keys": [
    "default-api-key-change-me",
    "my-secure-api-key-123"
  ]
}
```

**Wichtig:** Ändere den Default-Key in Produktionsumgebungen!

---

## 🐍 Python Client Beispiel

```python
import requests

BASE_URL = "http://localhost:5000/api"
API_KEY = "default-api-key-change-me"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# System-Status abrufen
response = requests.get(f"{BASE_URL}/system/status")
print(response.json())

# Pin setzen
response = requests.post(
    f"{BASE_URL}/pins/D13",
    headers=headers,
    json={"pin": "D13", "value": 1}
)
print(response.json())

# Sensor-Daten abrufen
response = requests.get(f"{BASE_URL}/sensors/B24_TEMP")
print(response.json())

# Sequenz starten
response = requests.post(
    f"{BASE_URL}/sequences/seq_1/start",
    headers=headers
)
print(response.json())
```

---

## 📱 CORS

CORS ist aktiviert für alle Origins (`*`). In Produktionsumgebungen sollte dies eingeschränkt werden.

---

## 🐛 Fehlerbehandlung

### HTTP Status Codes

- **200 OK**: Erfolgreiche Anfrage
- **401 Unauthorized**: Ungültiger oder fehlender API Key
- **404 Not Found**: Ressource nicht gefunden
- **503 Service Unavailable**: Server nicht bereit

### Fehler-Format

```json
{
  "error": "Invalid or missing API key"
}
```

---

## 🔧 Konfiguration

### Port ändern

In `api/rest_server.py`:

```python
self.rest_api = ArduinoRestAPI(host="0.0.0.0", port=8080)
```

### Logging

API-Logs werden im Standard-Logger ausgegeben:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

---

## 🚦 Verwendungsbeispiele

### Home Automation Integration

```python
# Home Assistant REST Sensor
sensor:
  - platform: rest
    name: "Arduino Temperatur"
    resource: "http://localhost:5000/api/sensors/B24_TEMP"
    value_template: "{{ value_json.value }}"
    unit_of_measurement: "°C"
```

### Monitoring mit Grafana

```python
# Prometheus Exporter
from prometheus_client import Gauge
import requests

temp_gauge = Gauge('arduino_temperature', 'Temperature from B24 Sensor')

def update_metrics():
    response = requests.get('http://localhost:5000/api/sensors/B24_TEMP')
    data = response.json()
    temp_gauge.set(data['value'])
```

---

## 📖 Weitere Informationen

- **Swagger UI**: http://localhost:5000/api/docs
- **OpenAPI Spec**: http://localhost:5000/api/swagger.json
- **GitHub**: https://github.com/Grown2206/Arduino-Control-Panel

---

**Version:** 1.0.0
**Erstellt mit:** Flask-RESTX, SocketIO
**Dokumentation:** Swagger/OpenAPI 3.0
