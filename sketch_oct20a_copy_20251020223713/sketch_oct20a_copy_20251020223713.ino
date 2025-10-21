/*
 * ARDUINO CONTROL PANEL - ENHANCED FIRMWARE v3.3
 *
 * *** WICHTIGES UPDATE ***
 * Die I2C-Steuerung für das B37 LED-Board ist standardmäßig deaktiviert,
 * da sie den Arduino blockieren kann, wenn das Board nicht korrekt angeschlossen ist.
 *
 * UM DIE B37-STEUERUNG ZU AKTIVIEREN:
 * 1. Stellen Sie sicher, dass das B37-Board korrekt an 5V, GND, A4 (SDA) und A5 (SCL) angeschlossen ist.
 * 2. Ändern Sie die folgende Zeile von "#define ENABLE_B37_SUPPORT 0" zu "#define ENABLE_B37_SUPPORT 1".
 * 3. Laden Sie den Sketch erneut auf den Arduino hoch.
 */
#define ENABLE_B37_SUPPORT 1

#include <ArduinoJson.h>
#include <DHT.h>
#include <Servo.h>

#if ENABLE_B37_SUPPORT == 1
#include <Wire.h>
#endif


// === SENSOR DEFINITIONEN ===
// HINWEIS: DHTPIN wurde auf 7 geändert, um Konflikt mit PWM/Servo auf Pin 3 zu vermeiden.
#define DHTPIN 7
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

#define VIBRATION_PIN 2

// HC-SR04 Ultraschall
#define TRIG_PIN 9
#define ECHO_PIN 10

// LDR Lichtsensor
#define LDR_PIN A0

#if ENABLE_B37_SUPPORT == 1
// === 8-LED B37 I2C ANSCHLÜSSE ===
// Board     -> Arduino Uno
// VCC / +5V -> 5V
// GND       -> GND
// SCL       -> A5 (SCL)
// SDA       -> A4 (SDA)
#define B37_I2C_ADDR 0x20
#endif

// === SERVO DEFINITIONEN ===
Servo servos[6];  // Bis zu 6 Servos
bool servoAttached[6] = {false, false, false, false, false, false};

void setup() {
  Serial.begin(115200);
  
#if ENABLE_B37_SUPPORT == 1
  Wire.begin(); // I2C initialisieren
#endif
  
  // DHT initialisieren
  dht.begin();
  
  // Vibrationssensor
  pinMode(VIBRATION_PIN, INPUT);
  
  // Ultraschall-Sensor
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Alle Digital Pins als Input
  for (int i = 0; i <= 13; i++) {
    pinMode(i, INPUT);
  }
  
  sendStatus("Arduino Enhanced System v3.3 gestartet");
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
  
  // === PWM COMMAND ===
  else if (command == "analog_write") {
    analogWritePin(doc["pin"], doc["value"], msgId);
  }
  
  // === SERVO COMMANDS ===
  else if (command == "servo_attach") {
    servoAttach(doc["pin"], msgId);
  }
  else if (command == "servo_write") {
    servoWrite(doc["pin"], doc["angle"], msgId);
  }
  else if (command == "servo_detach") {
    servoDetach(doc["pin"], msgId);
  }
  
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
    sendResponse(msgId, "ok");
  }
  
#if ENABLE_B37_SUPPORT == 1
  // === 8-LED B37 COMMAND ===
  else if (command == "write_b37") {
    int mask = doc["mask"];
    writeToB37(mask, msgId);
  }
#endif
  
  else if (command == "get_pin_states") {
    sendPinStates(msgId);
  }
  
  else {
    sendResponse(msgId, "unknown_command");
  }
}

#if ENABLE_B37_SUPPORT == 1
// === I2C B37 FUNCTION ===
void writeToB37(int mask, String msgId) {
  // Der PCF8574 ist "active low", d.h. eine 0 schaltet die LED an.
  // Wir müssen die Bitmaske invertieren.
  byte inverted_mask = ~mask;
  
  Wire.beginTransmission(B37_I2C_ADDR);
  Wire.write(inverted_mask);
  byte error = Wire.endTransmission();
  
  if (error == 0) {
    sendResponse(msgId, "ok");
  } else {
    sendResponse(msgId, "i2c_error");
  }
}
#endif


// === BASIC PIN FUNCTIONS ===

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

// === PWM FUNCTION ===

void analogWritePin(String pinStr, int value, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0) {
    sendResponse(msgId, "invalid_pin");
    return;
  }
  
  // PWM nur auf bestimmten Pins (3, 5, 6, 9, 10, 11 beim Uno)
  if (pin != 3 && pin != 5 && pin != 6 && pin != 9 && pin != 10 && pin != 11) {
    sendResponse(msgId, "not_pwm_pin");
    return;
  }
  
  analogWrite(pin, value);
  sendResponse(msgId, "ok");
  sendPinUpdate(pinStr, value);
}

// === SERVO FUNCTIONS ===

void servoAttach(String pinStr, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0 || pin > 13) {
    sendResponse(msgId, "invalid_pin");
    return;
  }
  
  // Servo an Pin attachieren
  if (!servoAttached[pin]) {
    servos[pin].attach(pin);
    servoAttached[pin] = true;
  }
  
  sendResponse(msgId, "ok");
}

void servoWrite(String pinStr, int angle, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0 || pin > 13) {
    sendResponse(msgId, "invalid_pin");
    return;
  }
  
  // Servo attachieren falls noch nicht geschehen
  if (!servoAttached[pin]) {
    servos[pin].attach(pin);
    servoAttached[pin] = true;
  }
  
  // Winkel begrenzen
  angle = constrain(angle, 0, 180);
  
  servos[pin].write(angle);
  sendResponse(msgId, "ok");
}

void servoDetach(String pinStr, String msgId) {
  int pin = pinToNumber(pinStr);
  if (pin < 0 || pin > 13) {
    sendResponse(msgId, "invalid_pin");
    return;
  }
  
  if (servoAttached[pin]) {
    servos[pin].detach();
    servoAttached[pin] = false;
  }
  
  sendResponse(msgId, "ok");
}

// === SENSOR FUNCTIONS ===

void readTempHumiditySensor() {
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

void readVibrationSensor() {
  bool isVibrating = digitalRead(VIBRATION_PIN);
  int intensity = isVibrating ? 100 : 0;

  JsonDocument doc;
  doc["type"] = "sensor_update";
  doc["sensor"] = "B39_VIBRATION";
  doc["intensity"] = intensity;
  doc["vibrating"] = isVibrating;
  serializeJson(doc, Serial);
  Serial.println();
}

void readUltrasonicSensor() {
  // HC-SR04 Messung
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
  float distance = duration * 0.034 / 2; // cm
  
  // Nur gültige Werte senden (2-400cm)
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

