/*
 * ARDUINO CONTROL PANEL - FIRMWARE v4.0 WORKING
 * Basiert auf v3.1, erweitert für GUI Kompatibilität
 * 
 * Features:
 * - Digital & Analog I/O (wie v3.1)
 * - DHT11/DHT22 Temperatur/Luftfeuchtigkeit
 * - HC-SR04 Ultraschall-Sensor
 * - Vibrationssensor
 * - LDR Lichtsensor
 * - NEU: Akzeptiert configure_sensors Befehl (ignoriert ihn aber)
 */

#include <ArduinoJson.h>
#include <DHT.h>

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

  sendStatus("Arduino System v4.0 WORKING gestartet");
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

  // === NEU: KONFIGURATIONSBEFEHLE (werden akzeptiert aber nichts gemacht) ===
  else if (command == "configure_sensors") {
    // GUI sendet das beim Verbinden - einfach OK zurück
    sendResponse(msgId, "ok");
    sendStatus("Sensor-Konfiguration empfangen");
  }
  else if (command == "configure_sensor_pin") {
    // GUI könnte das auch senden - einfach OK zurück
    sendResponse(msgId, "ok");
  }

  // === SENSOR COMMANDS ===
  else if (command == "read_sensor") {
    String sensor = doc["sensor"];
    
    // Alte Sensor-Namen von v3.1
    if (sensor == "B24_TEMP_HUMIDITY") {
      readTempHumiditySensor();
    } 
    else if (sensor == "B39_VIBRATION") {
      readVibrationSensor();
    } 
    else if (sensor == "HC_SR04") {
      readUltrasonicSensor();
    } 
    else if (sensor == "LDR") {
      readLDRSensor();
    }
    // Neue Sensor-Namen von v4.0
    else if (sensor == "DHT11" || sensor == "DHT22") {
      readTempHumiditySensor();
    }
    else if (sensor == "VIBRATION_SW420") {
      readVibrationSensor();
    }
    else if (sensor == "LM35") {
      readLM35Sensor();
    }
    else {
      // Unbekannter Sensor - trotzdem OK zurück
      sendResponse(msgId, "ok");
    }
    
    sendResponse(msgId, "ok");
  }

  else if (command == "get_pin_states") {
    sendPinStates(msgId);
  }

  else {
    sendResponse(msgId, "unknown_command");
  }
}

// === BASIC PIN FUNCTIONS ===

void setPinMode(String pinStr, String mode, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { 
    sendResponse(msgId, "invalid_pin"); 
    return; 
  }
  
  if (mode == "OUTPUT") {
    pinMode(pin, OUTPUT);
  }
  else if (mode == "INPUT") {
    pinMode(pin, INPUT);
  }
  else if (mode == "INPUT_PULLUP") {
    pinMode(pin, INPUT_PULLUP);
  }
  else { 
    sendResponse(msgId, "invalid_mode"); 
    return; 
  }
  
  sendResponse(msgId, "ok");
}

void digitalWritePin(String pinStr, int value, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { 
    sendResponse(msgId, "invalid_pin"); 
    return; 
  }
  
  digitalWrite(pin, value);
  sendResponse(msgId, "ok");
  sendPinUpdate(pinStr, value);
}

void digitalReadPin(String pinStr, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { 
    sendResponse(msgId, "invalid_pin"); 
    return; 
  }
  
  int value = digitalRead(pin);
  JsonDocument doc;
  doc["type"] = "response";
  doc["status"] = "ok";
  doc["response_to"] = msgId;
  doc["value"] = value;
  serializeJson(doc, Serial);
  Serial.println();
  sendPinUpdate(pinStr, value);
}

void analogReadPin(String pinStr, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { 
    sendResponse(msgId, "invalid_pin"); 
    return; 
  }
  
  int value = analogRead(pin);
  JsonDocument doc;
  doc["type"] = "response";
  doc["status"] = "ok";
  doc["response_to"] = msgId;
  doc["value"] = value;
  serializeJson(doc, Serial);
  Serial.println();
  sendPinUpdate(pinStr, value);
}

// === SENSOR FUNCTIONS ===

void readTempHumiditySensor() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (!isnan(temperature)) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "DHT11";
    doc["value"] = temperature;
    doc["unit"] = "°C";
    serializeJson(doc, Serial);
    Serial.println();
  }
  
  if (!isnan(humidity)) {
    JsonDocument doc;
    doc["type"] = "sensor_update";
    doc["sensor"] = "DHT11_HUMIDITY";
    doc["value"] = humidity;
    doc["unit"] = "%";
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void readVibrationSensor() {
  bool isVibrating = digitalRead(VIBRATION_PIN);
  int intensity = isVibrating ? 100 : 0;
  
  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "VIBRATION_SW420";
  doc["intensity"] = intensity;
  doc["vibrating"] = isVibrating;
  serializeJson(doc, Serial);
  Serial.println();
}

void readUltrasonicSensor() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
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

void readLDRSensor() {
  int lightLevel = analogRead(LDR_PIN);
  
  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "LDR";
  doc["value"] = lightLevel;
  doc["unit"] = "raw";
  serializeJson(doc, Serial);
  Serial.println();
}

void readLM35Sensor() {
  int rawValue = analogRead(LDR_PIN); // Nutze A0 als Standard
  float voltage = rawValue * (5.0 / 1024.0);
  float temperature = voltage * 100.0;
  
  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "LM35";
  doc["value"] = temperature;
  doc["unit"] = "°C";
  serializeJson(doc, Serial);
  Serial.println();
}

// === HELPER FUNCTIONS ===

void sendPinStates(String msgId) {
  JsonDocument doc;
  doc["type"] = "pin_states";
  doc["response_to"] = msgId;
  
  JsonArray digital = doc["digital"].to<JsonArray>();
  for (int i = 0; i <= 13; i++) {
    JsonObject pin = digital.add<JsonObject>();
    pin["pin"] = "D" + String(i);
    pin["value"] = digitalRead(i);
  }
  
  JsonArray analog = doc["analog"].to<JsonArray>();
  for (int i = 0; i <= 5; i++) {
    JsonObject pin = analog.add<JsonObject>();
    pin["pin"] = "A" + String(i);
    pin["value"] = analogRead(A0 + i);
  }
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendResponse(String msgId, String status) {
  JsonDocument doc;
  doc["type"] = "response";
  doc["status"] = status;
  doc["response_to"] = msgId;
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
  Serial.flush();  // WICHTIG: Warte bis Daten gesendet!
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

int pinToNumber(String pinStr) {
  if (pinStr.startsWith("D")) {
    int num = pinStr.substring(1).toInt();
    if (num >= 0 && num <= 13) return num;
  }
  else if (pinStr.startsWith("A")) {
    int num = pinStr.substring(1).toInt();
    if (num >= 0 && num <= 5) return A0 + num;
  }
  return -1;
}