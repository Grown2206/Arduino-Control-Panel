/*
 * ============================================================================
 * ARDUINO CONTROL PANEL - PROFESSIONAL FIRMWARE v4.0
 * ============================================================================
 *
 * Kompatibel mit: Drexler Dynamics Arduino Control Panel (Python/PyQt6)
 *
 * FEATURES:
 * ✅ Digital I/O (Pin-Modus, Read/Write)
 * ✅ Analog I/O (Read)
 * ✅ Dynamische Sensor-Konfiguration
 * ✅ DHT11/DHT22 Temperatur & Luftfeuchtigkeit
 * ✅ HC-SR04 Ultraschall-Distanzsensor
 * ✅ LDR Lichtsensor
 * ✅ Vibrationssensor
 * ✅ JSON-basierte Kommunikation
 * ✅ Fehlerbehandlung & Validation
 * ✅ Erweiterbar für weitere Sensoren
 *
 * KOMMUNIKATIONSPROTOKOLL:
 * - Baudrate: 115200
 * - Format: JSON (newline-terminated)
 * - Encoding: UTF-8
 *
 * DEPENDENCIES:
 * - ArduinoJson (v7.x): https://arduinojson.org/
 * - DHT Sensor Library: https://github.com/adafruit/DHT-sensor-library
 *
 * AUTHOR: Drexler Dynamics / Claude Code
 * VERSION: 4.0
 * DATE: 2024-10-24
 * ============================================================================
 */

#include <ArduinoJson.h>
#include <DHT.h>

// ============================================================================
// KONFIGURATION
// ============================================================================

#define SERIAL_BAUDRATE 115200
#define JSON_DOC_SIZE 512
#define MAX_SENSORS 10

// Default Sensor-Pins (überschreibbar via configure_sensor_pin)
#define DEFAULT_DHT_PIN 3
#define DEFAULT_DHT_TYPE DHT11
#define DEFAULT_VIBRATION_PIN 2
#define DEFAULT_TRIG_PIN 9
#define DEFAULT_ECHO_PIN 10
#define DEFAULT_LDR_PIN A0

// ============================================================================
// SENSOR-KONFIGURATION (dynamisch)
// ============================================================================

struct SensorConfig {
  String sensor_type;     // "DHT11", "DHT22", "HC_SR04", "LDR", "VIBRATION"
  int data_pin;          // Haupt-Daten-Pin
  int extra_pin;         // Extra-Pin (z.B. ECHO für HC-SR04)
  bool enabled;
  DHT* dht_instance;     // Für DHT-Sensoren
};

SensorConfig sensors[MAX_SENSORS];
int sensor_count = 0;

// Fallback für Basis-Sensoren (wenn nicht konfiguriert)
DHT default_dht(DEFAULT_DHT_PIN, DEFAULT_DHT_TYPE);
bool default_sensors_initialized = false;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(SERIAL_BAUDRATE);

  // Warte auf serielle Verbindung (wichtig für USB-Boards)
  while (!Serial && millis() < 3000) {
    ; // Timeout nach 3 Sekunden
  }

  // Initialisiere alle Digital-Pins als Input (sicher)
  for (int i = 0; i <= 13; i++) {
    pinMode(i, INPUT);
  }

  // Initialisiere Default-Sensoren (fallback)
  initializeDefaultSensors();

  // Sende Startup-Nachricht
  sendStatus("Arduino Control Panel v4.0 bereit");

  // Sende Pin-Konfiguration
  delay(100);
  sendPinConfiguration();
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.length() > 0) {
      processCommand(input);
    }
  }
}

// ============================================================================
// COMMAND PROCESSING
// ============================================================================

void processCommand(String input) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, input);

  if (error) {
    sendError("JSON Parse Error: " + String(error.c_str()));
    return;
  }

  // Extrahiere Command und ID
  String command = doc["command"] | "";
  String msgId = doc["id"] | "unknown";

  if (command.length() == 0) {
    sendResponse(msgId, "error", "Missing 'command' field");
    return;
  }

  // === BASIC PIN COMMANDS ===
  if (command == "pin_mode") {
    handlePinMode(doc, msgId);
  }
  else if (command == "digital_write") {
    handleDigitalWrite(doc, msgId);
  }
  else if (command == "digital_read") {
    handleDigitalRead(doc, msgId);
  }
  else if (command == "analog_read") {
    handleAnalogRead(doc, msgId);
  }

  // === SENSOR COMMANDS ===
  else if (command == "configure_sensor_pin") {
    handleConfigureSensor(doc, msgId);
  }
  else if (command == "read_sensor") {
    handleReadSensor(doc, msgId);
  }

  // === SYSTEM COMMANDS ===
  else if (command == "get_pin_states") {
    handleGetPinStates(msgId);
  }
  else if (command == "reset") {
    handleReset(msgId);
  }

  // === UNKNOWN COMMAND ===
  else {
    sendResponse(msgId, "error", "Unknown command: " + command);
  }
}

// ============================================================================
// PIN COMMAND HANDLERS
// ============================================================================

void handlePinMode(JsonDocument& doc, String msgId) {
  String pinStr = doc["pin"] | "";
  String mode = doc["mode"] | "";

  int pin = pinToNumber(pinStr);
  if (pin < 0) {
    sendResponse(msgId, "error", "Invalid pin: " + pinStr);
    return;
  }

  // Setze Pin-Modus
  if (mode == "OUTPUT") {
    pinMode(pin, OUTPUT);
  } else if (mode == "INPUT") {
    pinMode(pin, INPUT);
  } else if (mode == "INPUT_PULLUP") {
    pinMode(pin, INPUT_PULLUP);
  } else {
    sendResponse(msgId, "error", "Invalid mode: " + mode);
    return;
  }

  sendResponse(msgId, "ok");
}

void handleDigitalWrite(JsonDocument& doc, String msgId) {
  String pinStr = doc["pin"] | "";
  int value = doc["value"] | -1;

  int pin = pinToNumber(pinStr);
  if (pin < 0) {
    sendResponse(msgId, "error", "Invalid pin: " + pinStr);
    return;
  }

  if (value != 0 && value != 1) {
    sendResponse(msgId, "error", "Invalid value (must be 0 or 1)");
    return;
  }

  digitalWrite(pin, value);
  sendResponse(msgId, "ok");

  // Sende Pin-Update zurück
  sendPinUpdate(pinStr, value);
}

void handleDigitalRead(JsonDocument& doc, String msgId) {
  String pinStr = doc["pin"] | "";

  int pin = pinToNumber(pinStr);
  if (pin < 0) {
    sendResponse(msgId, "error", "Invalid pin: " + pinStr);
    return;
  }

  int value = digitalRead(pin);

  // Sende Response mit Wert
  JsonDocument response;
  response["type"] = "response";
  response["status"] = "ok";
  response["response_to"] = msgId;
  response["value"] = value;
  serializeJson(response, Serial);
  Serial.println();

  // Sende Pin-Update
  sendPinUpdate(pinStr, value);
}

void handleAnalogRead(JsonDocument& doc, String msgId) {
  String pinStr = doc["pin"] | "";

  int pin = pinToNumber(pinStr);
  if (pin < 0 || pin < A0) {
    sendResponse(msgId, "error", "Invalid analog pin: " + pinStr);
    return;
  }

  int value = analogRead(pin);

  // Sende Response mit Wert
  JsonDocument response;
  response["type"] = "response";
  response["status"] = "ok";
  response["response_to"] = msgId;
  response["value"] = value;
  serializeJson(response, Serial);
  Serial.println();

  // Sende Pin-Update
  sendPinUpdate(pinStr, value);
}

// ============================================================================
// SENSOR COMMAND HANDLERS
// ============================================================================

void handleConfigureSensor(JsonDocument& doc, String msgId) {
  String sensor_type = doc["sensor_type"] | "";
  JsonObject pin_config = doc["pin_config"];

  if (sensor_type.length() == 0) {
    sendResponse(msgId, "error", "Missing sensor_type");
    return;
  }

  // Finde freien Sensor-Slot
  if (sensor_count >= MAX_SENSORS) {
    sendResponse(msgId, "error", "Maximum sensors reached");
    return;
  }

  // Konfiguriere Sensor
  SensorConfig* sensor = &sensors[sensor_count];
  sensor->sensor_type = sensor_type;
  sensor->enabled = true;

  // Extrahiere Pin-Konfiguration
  if (sensor_type == "DHT11" || sensor_type == "DHT22") {
    String data_pin_str = pin_config["data"] | "D3";
    sensor->data_pin = pinToNumber(data_pin_str);

    // Erstelle DHT-Instanz
    uint8_t dht_type = (sensor_type == "DHT22") ? DHT22 : DHT11;
    sensor->dht_instance = new DHT(sensor->data_pin, dht_type);
    sensor->dht_instance->begin();

  } else if (sensor_type == "HC_SR04") {
    String trig_pin_str = pin_config["trigger"] | "D9";
    String echo_pin_str = pin_config["echo"] | "D10";
    sensor->data_pin = pinToNumber(trig_pin_str);
    sensor->extra_pin = pinToNumber(echo_pin_str);

    pinMode(sensor->data_pin, OUTPUT);
    pinMode(sensor->extra_pin, INPUT);

  } else if (sensor_type == "LDR") {
    String analog_pin_str = pin_config["analog"] | "A0";
    sensor->data_pin = pinToNumber(analog_pin_str);

  } else if (sensor_type == "VIBRATION") {
    String data_pin_str = pin_config["data"] | "D2";
    sensor->data_pin = pinToNumber(data_pin_str);
    pinMode(sensor->data_pin, INPUT);

  } else {
    sendResponse(msgId, "error", "Unknown sensor type: " + sensor_type);
    return;
  }

  sensor_count++;
  sendResponse(msgId, "ok");
}

void handleReadSensor(JsonDocument& doc, String msgId) {
  String sensor = doc["sensor"] | "";

  if (sensor.length() == 0) {
    sendResponse(msgId, "error", "Missing sensor field");
    return;
  }

  // Suche konfigurierten Sensor
  bool found = false;
  for (int i = 0; i < sensor_count; i++) {
    if (sensors[i].enabled) {
      String type = sensors[i].sensor_type;

      if (sensor == "B24_TEMP_HUMIDITY" && (type == "DHT11" || type == "DHT22")) {
        readDHTSensor(&sensors[i]);
        found = true;
        break;
      } else if (sensor == "HC_SR04" && type == "HC_SR04") {
        readUltrasonicSensor(&sensors[i]);
        found = true;
        break;
      } else if (sensor == "LDR" && type == "LDR") {
        readLDRSensor(&sensors[i]);
        found = true;
        break;
      } else if (sensor == "B39_VIBRATION" && type == "VIBRATION") {
        readVibrationSensor(&sensors[i]);
        found = true;
        break;
      }
    }
  }

  // Fallback zu Default-Sensoren
  if (!found && default_sensors_initialized) {
    if (sensor == "B24_TEMP_HUMIDITY") {
      readDefaultDHT();
      found = true;
    } else if (sensor == "HC_SR04") {
      readDefaultUltrasonic();
      found = true;
    } else if (sensor == "LDR") {
      readDefaultLDR();
      found = true;
    } else if (sensor == "B39_VIBRATION") {
      readDefaultVibration();
      found = true;
    }
  }

  if (found) {
    sendResponse(msgId, "ok");
  } else {
    sendResponse(msgId, "error", "Sensor not configured: " + sensor);
  }
}

// ============================================================================
// SYSTEM COMMAND HANDLERS
// ============================================================================

void handleGetPinStates(String msgId) {
  JsonDocument doc;
  doc["type"] = "pin_states";
  doc["response_to"] = msgId;

  // Digital Pins
  JsonArray digital = doc["digital"].to<JsonArray>();
  for (int i = 0; i <= 13; i++) {
    JsonObject pin = digital.add<JsonObject>();
    pin["pin"] = "D" + String(i);
    pin["value"] = digitalRead(i);
  }

  // Analog Pins
  JsonArray analog = doc["analog"].to<JsonArray>();
  for (int i = 0; i <= 5; i++) {
    JsonObject pin = analog.add<JsonObject>();
    pin["pin"] = "A" + String(i);
    pin["value"] = analogRead(A0 + i);
  }

  serializeJson(doc, Serial);
  Serial.println();
}

void handleReset(String msgId) {
  // Deaktiviere alle Sensoren
  for (int i = 0; i < sensor_count; i++) {
    if (sensors[i].dht_instance != nullptr) {
      delete sensors[i].dht_instance;
    }
    sensors[i].enabled = false;
  }
  sensor_count = 0;

  // Initialisiere Default-Sensoren neu
  initializeDefaultSensors();

  sendResponse(msgId, "ok");
  sendStatus("System reset - zurück zu Defaults");
}

// ============================================================================
// SENSOR READ FUNCTIONS (Konfigurierte Sensoren)
// ============================================================================

void readDHTSensor(SensorConfig* sensor) {
  if (sensor->dht_instance == nullptr) return;

  float temperature = sensor->dht_instance->readTemperature();
  float humidity = sensor->dht_instance->readHumidity();

  if (!isnan(temperature)) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "B24_TEMP";
    doc["value"] = temperature;
    serializeJson(doc, Serial);
    Serial.println();
  }

  if (!isnan(humidity)) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "B24_HUMIDITY";
    doc["value"] = humidity;
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void readUltrasonicSensor(SensorConfig* sensor) {
  digitalWrite(sensor->data_pin, LOW);
  delayMicroseconds(2);
  digitalWrite(sensor->data_pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(sensor->data_pin, LOW);

  long duration = pulseIn(sensor->extra_pin, HIGH, 30000);
  float distance = duration * 0.034 / 2;

  if (distance >= 2 && distance <= 400) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "HC_SR04";
    doc["value"] = distance;
    doc["unit"] = "cm";
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void readLDRSensor(SensorConfig* sensor) {
  int lightLevel = analogRead(sensor->data_pin);

  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "LDR";
  doc["value"] = lightLevel;
  doc["unit"] = "raw";
  serializeJson(doc, Serial);
  Serial.println();
}

void readVibrationSensor(SensorConfig* sensor) {
  bool isVibrating = digitalRead(sensor->data_pin);
  int intensity = isVibrating ? 100 : 0;

  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "B39_VIBRATION";
  doc["intensity"] = intensity;
  doc["vibrating"] = isVibrating;
  serializeJson(doc, Serial);
  Serial.println();
}

// ============================================================================
// DEFAULT SENSOR FUNCTIONS (Fallback)
// ============================================================================

void initializeDefaultSensors() {
  default_dht.begin();
  pinMode(DEFAULT_VIBRATION_PIN, INPUT);
  pinMode(DEFAULT_TRIG_PIN, OUTPUT);
  pinMode(DEFAULT_ECHO_PIN, INPUT);
  default_sensors_initialized = true;
}

void readDefaultDHT() {
  float temperature = default_dht.readTemperature();
  float humidity = default_dht.readHumidity();

  if (!isnan(temperature)) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "B24_TEMP";
    doc["value"] = temperature;
    serializeJson(doc, Serial);
    Serial.println();
  }

  if (!isnan(humidity)) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "B24_HUMIDITY";
    doc["value"] = humidity;
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void readDefaultUltrasonic() {
  digitalWrite(DEFAULT_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(DEFAULT_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(DEFAULT_TRIG_PIN, LOW);

  long duration = pulseIn(DEFAULT_ECHO_PIN, HIGH, 30000);
  float distance = duration * 0.034 / 2;

  if (distance >= 2 && distance <= 400) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "HC_SR04";
    doc["value"] = distance;
    doc["unit"] = "cm";
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void readDefaultLDR() {
  int lightLevel = analogRead(DEFAULT_LDR_PIN);

  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "LDR";
  doc["value"] = lightLevel;
  doc["unit"] = "raw";
  serializeJson(doc, Serial);
  Serial.println();
}

void readDefaultVibration() {
  bool isVibrating = digitalRead(DEFAULT_VIBRATION_PIN);
  int intensity = isVibrating ? 100 : 0;

  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "B39_VIBRATION";
  doc["intensity"] = intensity;
  doc["vibrating"] = isVibrating;
  serializeJson(doc, Serial);
  Serial.println();
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

int pinToNumber(String pinStr) {
  if (pinStr.startsWith("D")) {
    int num = pinStr.substring(1).toInt();
    if (num >= 0 && num <= 13) return num;
  } else if (pinStr.startsWith("A")) {
    int num = pinStr.substring(1).toInt();
    if (num >= 0 && num <= 5) return A0 + num;
  }
  return -1;
}

void sendResponse(String msgId, String status) {
  JsonDocument doc;
  doc["type"] = "response";
  doc["status"] = status;
  doc["response_to"] = msgId;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendResponse(String msgId, String status, String message) {
  JsonDocument doc;
  doc["type"] = "response";
  doc["status"] = status;
  doc["response_to"] = msgId;
  doc["message"] = message;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendPinUpdate(String pin, int value) {
  JsonDocument doc;
  doc["type"] = "pin_update";
  doc["pin_name"] = pin;
  doc["value"] = value;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendStatus(String message) {
  JsonDocument doc;
  doc["type"] = "status";
  doc["message"] = message;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendError(String error) {
  JsonDocument doc;
  doc["type"] = "error";
  doc["message"] = error;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendPinConfiguration() {
  JsonDocument doc;
  doc["type"] = "config";
  doc["version"] = "4.0";
  doc["board"] = "Arduino Uno/Nano";
  doc["digital_pins"] = 14;
  doc["analog_pins"] = 6;
  doc["baudrate"] = SERIAL_BAUDRATE;

  JsonArray supported = doc["supported_sensors"].to<JsonArray>();
  supported.add("DHT11");
  supported.add("DHT22");
  supported.add("HC_SR04");
  supported.add("LDR");
  supported.add("VIBRATION");

  serializeJson(doc, Serial);
  Serial.println();
}
