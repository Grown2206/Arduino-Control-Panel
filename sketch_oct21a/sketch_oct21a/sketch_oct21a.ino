/*
 * ARDUINO CONTROL PANEL - REDUCED FIRMWARE v3.1
 * Entfernt: PWM-Ausgabe (analog_write) und Servo-Steuerung
 *
 * Features:
 * - Digital & Analog I/O
 * - DHT11/DHT22 Temperatur/Luftfeuchtigkeit
 * - HC-SR04 Ultraschall-Sensor
 * - Vibrationssensor
 * - LDR Lichtsensor
 * - Erweiterbar für weitere Sensoren
 */

#include <ArduinoJson.h>
#include <DHT.h>
// REMOVED: #include <Servo.h>

// === SENSOR DEFINITIONEN ===
#define DHTPIN 3
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
#define VIBRATION_PIN 2

// HC-SR04 Ultraschall
#define TRIG_PIN 9
#define ECHO_PIN 10

// LDR Lichtsensor
#define LDR_PIN A0

// REMOVED: Servo Definitionen
// Servo servos[6];
// bool servoAttached[6] = {false, false, false, false, false, false};

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Alle Digital Pins als Input
  for (int i = 0; i <= 13; i++) {
    pinMode(i, INPUT);
  }

  sendStatus("Arduino Reduced System v3.1 gestartet");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() > 0) {
      processCommand(input);
    }
  }
}

void processCommand(String input) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, input);
  if (error) {
    sendError("JSON Parse Error");
    return;
  }

  String command = doc["command"];
  String msgId = doc["id"];

  // === BASIC COMMANDS ===
  if (command == "pin_mode") {
    setPinMode(doc["pin"], doc["mode"], msgId);
  }
  else if (command == "digital_write") {
    digitalWritePin(doc["pin"], doc["value"], msgId);
  }
  else if (command == "digital_read") {
    digitalReadPin(doc["pin"], msgId);
  }
  else if (command == "analog_read") {
    analogReadPin(doc["pin"], msgId);
  }

  // REMOVED: PWM COMMAND
  // else if (command == "analog_write") { ... }

  // REMOVED: SERVO COMMANDS
  // else if (command == "servo_attach") { ... }
  // else if (command == "servo_write") { ... }
  // else if (command == "servo_detach") { ... }

  // === SENSOR COMMANDS ===
  else if (command == "read_sensor") {
    String sensor = doc["sensor"];
    if (sensor == "B24_TEMP_HUMIDITY") {
      readTempHumiditySensor();
    } else if (sensor == "B39_VIBRATION") {
      readVibrationSensor();
    } else if (sensor == "HC_SR04") {
      readUltrasonicSensor();
    } else if (sensor == "LDR") {
      readLDRSensor();
    }
    sendResponse(msgId, "ok"); // Bestätigung nach Sensorabfrage
  }

  else if (command == "get_pin_states") {
    sendPinStates(msgId);
  }

  else {
    sendResponse(msgId, "unknown_command");
  }
}

// === BASIC PIN FUNCTIONS (Unverändert) ===

void setPinMode(String pinStr, String mode, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { sendResponse(msgId, "invalid_pin"); return; }
  if (mode == "OUTPUT") pinMode(pin, OUTPUT);
  else if (mode == "INPUT") pinMode(pin, INPUT);
  else if (mode == "INPUT_PULLUP") pinMode(pin, INPUT_PULLUP);
  else { sendResponse(msgId, "invalid_mode"); return; }
  sendResponse(msgId, "ok");
}

void digitalWritePin(String pinStr, int value, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { sendResponse(msgId, "invalid_pin"); return; }
  digitalWrite(pin, value);
  sendResponse(msgId, "ok");
  sendPinUpdate(pinStr, value); // Send update back
}

void digitalReadPin(String pinStr, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { sendResponse(msgId, "invalid_pin"); return; }
  int value = digitalRead(pin);
  JsonDocument doc;
  doc["type"] = "response"; doc["status"] = "ok"; doc["response_to"] = msgId; doc["value"] = value;
  serializeJson(doc, Serial); Serial.println();
  sendPinUpdate(pinStr, value); // Send update back
}

void analogReadPin(String pinStr, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { sendResponse(msgId, "invalid_pin"); return; }
  int value = analogRead(pin);
  JsonDocument doc;
  doc["type"] = "response"; doc["status"] = "ok"; doc["response_to"] = msgId; doc["value"] = value;
  serializeJson(doc, Serial); Serial.println();
  sendPinUpdate(pinStr, value); // Send update back
}

// REMOVED: PWM FUNCTION
// void analogWritePin(...) { ... }

// REMOVED: SERVO FUNCTIONS
// void servoAttach(...) { ... }
// void servoWrite(...) { ... }
// void servoDetach(...) { ... }

// === SENSOR FUNCTIONS (Unverändert) ===

void readTempHumiditySensor() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  if (!isnan(temperature)) {
    JsonDocument doc; doc["type"] = "sensor_update"; doc["sensor"] = "B24_TEMP"; doc["value"] = temperature;
    serializeJson(doc, Serial); Serial.println();
  }
  if (!isnan(humidity)) {
    JsonDocument doc; doc["type"] = "sensor_update"; doc["sensor"] = "B24_HUMIDITY"; doc["value"] = humidity;
    serializeJson(doc, Serial); Serial.println();
  }
}

void readVibrationSensor() {
  bool isVibrating = digitalRead(VIBRATION_PIN);
  int intensity = isVibrating ? 100 : 0;
  JsonDocument doc;
  doc["type"] = "sensor_update"; doc["sensor"] = "B39_VIBRATION"; doc["intensity"] = intensity; doc["vibrating"] = isVibrating;
  serializeJson(doc, Serial); Serial.println();
}

void readUltrasonicSensor() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
  float distance = duration * 0.034 / 2; // cm
  if (distance >= 2 && distance <= 400) {
    JsonDocument doc; doc["type"] = "sensor_update"; doc["sensor"] = "HC_SR04"; doc["value"] = distance; doc["unit"] = "cm";
    serializeJson(doc, Serial); Serial.println();
  }
}

void readLDRSensor() {
  int lightLevel = analogRead(LDR_PIN);
  JsonDocument doc; doc["type"] = "sensor_update"; doc["sensor"] = "LDR"; doc["value"] = lightLevel; doc["unit"] = "raw";
  serializeJson(doc, Serial); Serial.println();
}

// === HELPER FUNCTIONS (Unverändert) ===

void sendPinStates(String msgId) {
  JsonDocument doc; doc["type"] = "pin_states"; doc["response_to"] = msgId;
  JsonArray digital = doc["digital"].to<JsonArray>();
  for (int i = 0; i <= 13; i++) { JsonObject pin = digital.add<JsonObject>(); pin["pin"] = "D" + String(i); pin["value"] = digitalRead(i); }
  JsonArray analog = doc["analog"].to<JsonArray>();
  for (int i = 0; i <= 5; i++) { JsonObject pin = analog.add<JsonObject>(); pin["pin"] = "A" + String(i); pin["value"] = analogRead(A0 + i); }
  serializeJson(doc, Serial); Serial.println();
}

void sendResponse(String msgId, String status) {
  JsonDocument doc; doc["type"] = "response"; doc["status"] = status; doc["response_to"] = msgId;
  serializeJson(doc, Serial); Serial.println();
}

void sendPinUpdate(String pin, int value) {
  JsonDocument doc; doc["type"] = "pin_update"; doc["pin_name"] = pin; doc["value"] = value;
  serializeJson(doc, Serial); Serial.println();
}

void sendStatus(String message) {
  JsonDocument doc; doc["type"] = "status"; doc["message"] = message;
  serializeJson(doc, Serial); Serial.println();
}

void sendError(String error) {
  JsonDocument doc; doc["type"] = "error"; doc["message"] = error;
  serializeJson(doc, Serial); Serial.println();
}

int pinToNumber(String pinStr) {
  if (pinStr.startsWith("D")) { int num = pinStr.substring(1).toInt(); if (num >= 0 && num <= 13) return num; }
  else if (pinStr.startsWith("A")) { int num = pinStr.substring(1).toInt(); if (num >= 0 && num <= 5) return A0 + num; }
  return -1;
}