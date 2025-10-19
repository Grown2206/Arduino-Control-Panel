/*
 * ARDUINO CONTROL PANEL - SENSOR FIRMWARE v2.8
 * Angepasst für aktives Polling durch die PC-Anwendung.
 * * Reagiert auf den Befehl {"command": "read_sensor", "sensor": "..."}
 * Sendet Sensor-Daten nur auf Anfrage.
 * * Sensoren:
 * - B24: Temperatur/Luftfeuchtigkeit (3-Pin) an D3
 * - B39: Vibrationssensor an D2
 */

#include <ArduinoJson.h>
#include <DHT.h>

// B24 Sensor Setup (3-Pin Version)
#define DHTPIN 3
#define DHTTYPE DHT11  // Allnet B24 verwendet DHT11
DHT dht(DHTPIN, DHTTYPE);

// Vibrationssensor Pin
#define B39_PIN 2

void setup() {
  Serial.begin(115200);
  
  // DHT Sensor initialisieren
  dht.begin();
  
  // Vibrationssensor Pin
  pinMode(B39_PIN, INPUT);
  
  // Alle Digital Pins als Input setzen (Standard)
  for (int i = 0; i <= 13; i++) {
    pinMode(i, INPUT);
  }
  
  // Startup-Nachricht
  sendStatus("Arduino System gestartet - Bereit für Befehle.");
}

void loop() {
  // Nur noch auf Kommandos von Serial warten
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
  
  if (command == "pin_mode") {
    String pin = doc["pin"];
    String mode = doc["mode"];
    setPinMode(pin, mode, msgId);
  }
  else if (command == "digital_write") {
    String pin = doc["pin"];
    int value = doc["value"];
    digitalWritePin(pin, value, msgId);
  }
  else if (command == "digital_read") {
    String pin = doc["pin"];
    digitalReadPin(pin, msgId);
  }
  else if (command == "analog_read") {
    String pin = doc["pin"];
    analogReadPin(pin, msgId);
  }
  // KORREKTUR: Auf den neuen Befehl "read_sensor" reagieren
  else if (command == "read_sensor") {
    String sensor = doc["sensor"];
    if (sensor == "B39_VIBRATION") {
      readVibrationSensor();
    } else if (sensor == "B24_TEMP_HUMIDITY") {
      readTempHumiditySensor();
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

void setPinMode(String pinStr, String mode, String msgId) {
  int pin = pinToNumber(pinStr);
  
  if (pin < 0) {
    sendResponse(msgId, "invalid_pin");
    return;
  }
  
  if (mode == "OUTPUT") {
    pinMode(pin, OUTPUT);
  } else if (mode == "INPUT") {
    pinMode(pin, INPUT);
  } else if (mode == "INPUT_PULLUP") {
    pinMode(pin, INPUT_PULLUP);
  } else {
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

// KORREKTUR: Funktion liest nur noch Temp/Feuchtigkeit, wenn aufgerufen
void readTempHumiditySensor() {
  // B24: Temperatur und Luftfeuchtigkeit
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
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

// KORREKTUR: Funktion liest Vibration, wenn aufgerufen, und sendet IMMER den Status
void readVibrationSensor() {
  bool isVibrating = digitalRead(B39_PIN);
  int intensity = 0; // Einfache Intensität: 100 für Vibration, 0 für Ruhe

  if(isVibrating) {
    intensity = 100;
  }

  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "B39_VIBRATION";
  doc["intensity"] = intensity;
  doc["vibrating"] = isVibrating;
  serializeJson(doc, Serial);
  Serial.println();
}


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
