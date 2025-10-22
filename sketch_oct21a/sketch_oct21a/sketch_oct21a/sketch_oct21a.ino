/*
 * ARDUINO CONTROL PANEL - EXTENDED FIRMWARE v4.0
 * Unterstützt 40-in-1 Sensor Kit
 * 
 * Features:
 * - Dynamische Sensor-Konfiguration
 * - Digital & Analog I/O
 * - DHT11/DHT22 Temperatur/Luftfeuchtigkeit
 * - HC-SR04 Ultraschall-Sensor
 * - Alle analogen Sensoren (LM35, TMP36, LDR, etc.)
 * - Digitale Sensoren (PIR, Touch, Buttons, etc.)
 * - Erweiterbar für I2C Sensoren
 */

#include <ArduinoJson.h>
#include <DHT.h>

// === DYNAMISCHE SENSOR KONFIGURATION ===
struct SensorConfig {
  String id;
  String type;
  int pin1;
  int pin2;
  bool active;
};

SensorConfig activeSensors[10]; // Max 10 Sensoren gleichzeitig
int sensorCount = 0;

// DHT Sensoren
DHT* dhtSensor = nullptr;
int dhtPin = -1;
int dhtType = DHT11;

// HC-SR04 Pins
int trigPin = -1;
int echoPin = -1;

void setup() {
  Serial.begin(115200);
  
  // Alle Digital Pins als Input
  for (int i = 0; i <= 13; i++) {
    pinMode(i, INPUT);
  }
  
  sendStatus("Arduino Extended System v4.0 gestartet - 40 Sensoren unterstützt");
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
  
  // === SENSOR CONFIGURATION ===
  else if (command == "configure_sensors") {
    configureSensors(doc, msgId);
  }
  
  // === SENSOR COMMANDS ===
  else if (command == "read_sensor") {
    String sensor = doc["sensor"];
    readSensor(sensor, msgId);
  }
  
  else if (command == "get_pin_states") {
    sendPinStates(msgId);
  }
  
  else {
    sendResponse(msgId, "unknown_command");
  }
}

// === SENSOR CONFIGURATION ===
void configureSensors(JsonDocument& doc, String msgId) {
  // Reset alle Sensoren
  sensorCount = 0;
  if (dhtSensor != nullptr) {
    delete dhtSensor;
    dhtSensor = nullptr;
  }
  
  // Lade neue Konfiguration
  JsonObject sensors = doc["active_sensors"];
  
  for (JsonPair kv : sensors) {
    String sensorId = kv.key().c_str();
    JsonObject config = kv.value();
    String sensorType = config["sensor_type"];
    
    // DHT Sensoren
    if (sensorType == "DHT11" || sensorType == "DHT22") {
      JsonObject pins = config["pin_config"];
      dhtPin = pins["data"];
      dhtType = (sensorType == "DHT22") ? DHT22 : DHT11;
      dhtSensor = new DHT(dhtPin, dhtType);
      dhtSensor->begin();
      pinMode(dhtPin, INPUT);
      sendStatus("DHT Sensor konfiguriert auf Pin " + String(dhtPin));
    }
    
    // HC-SR04 Ultraschall
    else if (sensorType == "HC_SR04") {
      JsonObject pins = config["pin_config"];
      trigPin = pins["trigger"];
      echoPin = pins["echo"];
      pinMode(trigPin, OUTPUT);
      pinMode(echoPin, INPUT);
      sendStatus("HC-SR04 konfiguriert: Trigger=" + String(trigPin) + " Echo=" + String(echoPin));
    }
    
    // Alle anderen Sensoren (analog/digital)
    else {
      if (sensorCount < 10) {
        activeSensors[sensorCount].id = sensorId;
        activeSensors[sensorCount].type = sensorType;
        activeSensors[sensorCount].active = true;
        
        JsonObject pins = config["pin_config"];
        // Nimm den ersten Pin (für einfache Sensoren)
        for (JsonPair pin : pins) {
          activeSensors[sensorCount].pin1 = pin.value();
          break;
        }
        sensorCount++;
        sendStatus("Sensor " + sensorType + " konfiguriert");
      }
    }
  }
  
  sendResponse(msgId, "ok");
}

// === SENSOR READING ===
void readSensor(String sensorType, String msgId) {
  
  // DHT11 / DHT22
  if (sensorType == "DHT11" || sensorType == "DHT22") {
    if (dhtSensor != nullptr) {
      float temperature = dhtSensor->readTemperature();
      float humidity = dhtSensor->readHumidity();
      
      if (!isnan(temperature)) {
        JsonDocument doc;
        doc["type"] = "sensor_update";
        doc["sensor"] = sensorType;
        doc["value"] = temperature;
        doc["unit"] = "°C";
        serializeJson(doc, Serial);
        Serial.println();
      }
      
      if (!isnan(humidity)) {
        JsonDocument doc;
        doc["type"] = "sensor_update";
        doc["sensor"] = sensorType + "_HUMIDITY";
        doc["value"] = humidity;
        doc["unit"] = "%";
        serializeJson(doc, Serial);
        Serial.println();
      }
    }
    sendResponse(msgId, "ok");
    return;
  }
  
  // HC-SR04 Ultraschall
  if (sensorType == "HC_SR04") {
    if (trigPin >= 0 && echoPin >= 0) {
      digitalWrite(trigPin, LOW);
      delayMicroseconds(2);
      digitalWrite(trigPin, HIGH);
      delayMicroseconds(10);
      digitalWrite(trigPin, LOW);
      
      long duration = pulseIn(echoPin, HIGH, 30000);
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
    sendResponse(msgId, "ok");
    return;
  }
  
  // LM35 Analog Temperature
  if (sensorType == "LM35") {
    int pin = findSensorPin("LM35");
    if (pin >= 0) {
      int rawValue = analogRead(pin);
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
    sendResponse(msgId, "ok");
    return;
  }
  
  // TMP36 Analog Temperature
  if (sensorType == "TMP36") {
    int pin = findSensorPin("TMP36");
    if (pin >= 0) {
      int rawValue = analogRead(pin);
      float voltage = rawValue * (5.0 / 1024.0);
      float temperature = (voltage - 0.5) * 100.0;
      
      JsonDocument doc;
      doc["type"] = "sensor_update";
      doc["sensor"] = "TMP36";
      doc["value"] = temperature;
      doc["unit"] = "°C";
      serializeJson(doc, Serial);
      Serial.println();
    }
    sendResponse(msgId, "ok");
    return;
  }
  
  // LDR (Lichtsensor)
  if (sensorType == "LDR") {
    int pin = findSensorPin("LDR");
    if (pin >= 0) {
      int lightLevel = analogRead(pin);
      
      JsonDocument doc;
      doc["type"] = "sensor_update";
      doc["sensor"] = "LDR";
      doc["value"] = lightLevel;
      doc["unit"] = "raw";
      serializeJson(doc, Serial);
      Serial.println();
    }
    sendResponse(msgId, "ok");
    return;
  }
  
  // PIR Motion (HC-SR501)
  if (sensorType == "HC_SR501") {
    int pin = findSensorPin("HC_SR501");
    if (pin >= 0) {
      int motion = digitalRead(pin);
      
      JsonDocument doc;
      doc["type"] = "sensor_update";
      doc["sensor"] = "HC_SR501";
      doc["value"] = motion;
      doc["unit"] = "motion";
      serializeJson(doc, Serial);
      Serial.println();
    }
    sendResponse(msgId, "ok");
    return;
  }
  
  // Vibration Sensor (SW-420)
  if (sensorType == "VIBRATION_SW420" || sensorType == "B39_VIBRATION") {
    int pin = findSensorPin("VIBRATION_SW420");
    if (pin < 0) pin = findSensorPin("B39_VIBRATION");
    if (pin >= 0) {
      int vibration = digitalRead(pin);
      int intensity = vibration ? 100 : 0;
      
      JsonDocument doc;
      doc["type"] = "sensor_update";
      doc["sensor"] = "VIBRATION_SW420";
      doc["intensity"] = intensity;
      doc["vibrating"] = vibration;
      serializeJson(doc, Serial);
      Serial.println();
    }
    sendResponse(msgId, "ok");
    return;
  }
  
  // Generische digitale Sensoren (Button, Touch, Reed, Tilt, etc.)
  if (sensorType == "BUTTON_MODULE" || sensorType == "TOUCH_TTP223" || 
      sensorType == "REED_SWITCH" || sensorType == "TILT_SWITCH" ||
      sensorType == "LINE_TRACKING" || sensorType == "OBSTACLE_AVOIDANCE" ||
      sensorType == "FLAME_SENSOR" || sensorType == "HALL_A3144") {
    int pin = findSensorPin(sensorType);
    if (pin >= 0) {
      int value = digitalRead(pin);
      
      JsonDocument doc;
      doc["type"] = "sensor_update";
      doc["sensor"] = sensorType;
      doc["value"] = value;
      doc["unit"] = "digital";
      serializeJson(doc, Serial);
      Serial.println();
    }
    sendResponse(msgId, "ok");
    return;
  }
  
  // Generische analoge Sensoren (Hall 49E, Sound, Rain, Soil Moisture, MQ-2, etc.)
  if (sensorType == "HALL_49E" || sensorType == "SOUND_SENSOR" ||
      sensorType == "RAIN_SENSOR" || sensorType == "SOIL_MOISTURE" ||
      sensorType == "MQ2") {
    int pin = findSensorPin(sensorType);
    if (pin >= 0) {
      int value = analogRead(pin);
      
      JsonDocument doc;
      doc["type"] = "sensor_update";
      doc["sensor"] = sensorType;
      doc["value"] = value;
      doc["unit"] = "raw";
      serializeJson(doc, Serial);
      Serial.println();
    }
    sendResponse(msgId, "ok");
    return;
  }
  
  // Joystick
  if (sensorType == "JOYSTICK") {
    // Würde X, Y und Button lesen
    // Vereinfacht für Demo
    sendResponse(msgId, "ok");
    return;
  }
  
  // Unbekannter Sensor
  sendResponse(msgId, "unknown_sensor");
}

// Hilfsfunktion: Finde Pin für Sensor-Typ
int findSensorPin(String sensorType) {
  for (int i = 0; i < sensorCount; i++) {
    if (activeSensors[i].type == sensorType && activeSensors[i].active) {
      return activeSensors[i].pin1;
    }
  }
  return -1;
}

// === BASIC PIN FUNCTIONS ===
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
  sendPinUpdate(pinStr, value);
}

void digitalReadPin(String pinStr, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) { sendResponse(msgId, "invalid_pin"); return; }
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
  if (pin < 0) { sendResponse(msgId, "invalid_pin"); return; }
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