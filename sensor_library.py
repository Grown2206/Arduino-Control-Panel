# -*- coding: utf-8 -*-
"""
Sensor-Bibliothek für Arduino Control Panel
Unterstützt gängige Sensoren aus Arduino Starter Kits
"""

from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional
from enum import Enum

class SensorType(Enum):
    """Sensor-Kategorien"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    LIGHT = "light"
    MOTION = "motion"
    DISTANCE = "distance"
    SOUND = "sound"
    GAS = "gas"
    PRESSURE = "pressure"
    ACCELERATION = "acceleration"
    MAGNETIC = "magnetic"
    ROTATION = "rotation"
    TOUCH = "touch"
    WATER = "water"
    FLAME = "flame"

@dataclass
class SensorDefinition:
    """Definition eines Sensors"""
    id: str
    name: str
    sensor_type: SensorType
    pins: Dict[str, str]  # z.B. {"data": "D2", "vcc": "5V", "gnd": "GND"}
    protocol: str  # "digital", "analog", "i2c", "spi", "serial"
    value_range: tuple  # (min, max)
    unit: str
    read_interval_ms: int = 1000
    calibration_func: Optional[Callable] = None
    description: str = ""
    icon: str = "📊"

class SensorLibrary:
    """Vordefinierte Sensoren aus gängigen Arduino-Kits"""
    
    SENSORS = {
        # === TEMPERATUR & KLIMA ===
        "DHT11": SensorDefinition(
            id="DHT11",
            name="DHT11 Temperatur/Luftfeuchtigkeit",
            sensor_type=SensorType.TEMPERATURE,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(0, 50),
            unit="°C / %",
            icon="🌡️",
            description="Digitaler Temperatur- und Luftfeuchtigkeitssensor"
        ),
        
        "DHT22": SensorDefinition(
            id="DHT22",
            name="DHT22 Präzisions-Temp/Humidity",
            sensor_type=SensorType.TEMPERATURE,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(-40, 80),
            unit="°C / %",
            icon="🌡️",
            description="Hochpräziser Temperatur- und Feuchtigkeitssensor"
        ),
        
        "DS18B20": SensorDefinition(
            id="DS18B20",
            name="DS18B20 Wasserdichter Temp-Sensor",
            sensor_type=SensorType.TEMPERATURE,
            pins={"data": "D3"},
            protocol="onewire",
            value_range=(-55, 125),
            unit="°C",
            icon="🌊",
            description="Wasserdichter Temperatursensor (One-Wire)"
        ),
        
        "LM35": SensorDefinition(
            id="LM35",
            name="LM35 Analog Temperatur",
            sensor_type=SensorType.TEMPERATURE,
            pins={"analog": "A0"},
            protocol="analog",
            value_range=(-55, 150),
            unit="°C",
            calibration_func=lambda x: (x * 5.0 / 1024.0) * 100,
            icon="🌡️",
            description="Analoger Präzisions-Temperatursensor"
        ),
        
        "BMP180": SensorDefinition(
            id="BMP180",
            name="BMP180 Luftdruck/Temp",
            sensor_type=SensorType.PRESSURE,
            pins={"sda": "A4", "scl": "A5"},
            protocol="i2c",
            value_range=(300, 1100),
            unit="hPa",
            icon="🏔️",
            description="Barometrischer Drucksensor (I2C)"
        ),
        
        # === LICHT & FARBE ===
        "LDR": SensorDefinition(
            id="LDR",
            name="Fotowiderstand (LDR)",
            sensor_type=SensorType.LIGHT,
            pins={"analog": "A0"},
            protocol="analog",
            value_range=(0, 1023),
            unit="Lux",
            icon="💡",
            description="Lichtsensor (Light Dependent Resistor)"
        ),
        
        "BH1750": SensorDefinition(
            id="BH1750",
            name="BH1750 Digitaler Lichtsensor",
            sensor_type=SensorType.LIGHT,
            pins={"sda": "A4", "scl": "A5"},
            protocol="i2c",
            value_range=(1, 65535),
            unit="Lux",
            icon="☀️",
            description="Hochpräziser digitaler Lichtsensor"
        ),
        
        "TCS3200": SensorDefinition(
            id="TCS3200",
            name="TCS3200 RGB Farbsensor",
            sensor_type=SensorType.LIGHT,
            pins={"s0": "D2", "s1": "D3", "s2": "D4", "s3": "D5", "out": "D6"},
            protocol="digital",
            value_range=(0, 255),
            unit="RGB",
            icon="🌈",
            description="RGB-Farberkennungssensor"
        ),
        
        # === BEWEGUNG & POSITION ===
        "HC_SR501": SensorDefinition(
            id="HC_SR501",
            name="HC-SR501 PIR Bewegungsmelder",
            sensor_type=SensorType.MOTION,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(0, 1),
            unit="Bewegung",
            icon="🚶",
            description="Passiver Infrarot-Bewegungssensor"
        ),
        
        "HC_SR04": SensorDefinition(
            id="HC_SR04",
            name="HC-SR04 Ultraschall Distanz",
            sensor_type=SensorType.DISTANCE,
            pins={"trigger": "D9", "echo": "D10"},
            protocol="digital",
            value_range=(2, 400),
            unit="cm",
            icon="📏",
            description="Ultraschall-Entfernungsmesser"
        ),
        
        "MPU6050": SensorDefinition(
            id="MPU6050",
            name="MPU6050 Gyro/Beschleunigung",
            sensor_type=SensorType.ACCELERATION,
            pins={"sda": "A4", "scl": "A5"},
            protocol="i2c",
            value_range=(-32768, 32767),
            unit="m/s² / °/s",
            icon="🎢",
            description="6-Achsen Gyroskop + Beschleunigungssensor"
        ),
        
        "ADXL345": SensorDefinition(
            id="ADXL345",
            name="ADXL345 3-Achsen Beschleunigung",
            sensor_type=SensorType.ACCELERATION,
            pins={"sda": "A4", "scl": "A5"},
            protocol="i2c",
            value_range=(-16, 16),
            unit="g",
            icon="📐",
            description="Präziser 3-Achsen-Beschleunigungssensor"
        ),
        
        # === MAGNETFELD & ROTATION ===
        "HMC5883L": SensorDefinition(
            id="HMC5883L",
            name="HMC5883L Magnetkompass",
            sensor_type=SensorType.MAGNETIC,
            pins={"sda": "A4", "scl": "A5"},
            protocol="i2c",
            value_range=(0, 360),
            unit="°",
            icon="🧭",
            description="3-Achsen digitaler Kompass"
        ),
        
        "HALL_SENSOR": SensorDefinition(
            id="HALL_SENSOR",
            name="Hall-Effekt Magnetsensor",
            sensor_type=SensorType.MAGNETIC,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(0, 1),
            unit="Feld",
            icon="🧲",
            description="Erkennt Magnetfelder"
        ),
        
        "ROTARY_ENCODER": SensorDefinition(
            id="ROTARY_ENCODER",
            name="Drehgeber (Rotary Encoder)",
            sensor_type=SensorType.ROTATION,
            pins={"clk": "D2", "dt": "D3", "sw": "D4"},
            protocol="digital",
            value_range=(-999, 999),
            unit="Steps",
            icon="🎚️",
            description="Inkrementeller Drehgeber mit Taster"
        ),
        
        # === AUDIO ===
        "MIC_ANALOG": SensorDefinition(
            id="MIC_ANALOG",
            name="Mikrofon (Analog)",
            sensor_type=SensorType.SOUND,
            pins={"analog": "A0"},
            protocol="analog",
            value_range=(0, 1023),
            unit="dB",
            icon="🎤",
            description="Analoges Mikrofon-Modul"
        ),
        
        "SOUND_SENSOR": SensorDefinition(
            id="SOUND_SENSOR",
            name="KY-037 Schallsensor",
            sensor_type=SensorType.SOUND,
            pins={"digital": "D2", "analog": "A0"},
            protocol="analog",
            value_range=(0, 1023),
            unit="Level",
            icon="🔊",
            description="Schallpegel-Sensor mit digital/analog"
        ),
        
        # === GAS & QUALITÄT ===
        "MQ2": SensorDefinition(
            id="MQ2",
            name="MQ-2 Rauch/Gas-Sensor",
            sensor_type=SensorType.GAS,
            pins={"analog": "A0", "digital": "D2"},
            protocol="analog",
            value_range=(0, 1023),
            unit="ppm",
            icon="💨",
            description="Erkennt Rauch, LPG, Propan, Methan, CO"
        ),
        
        "MQ135": SensorDefinition(
            id="MQ135",
            name="MQ-135 Luftqualität",
            sensor_type=SensorType.GAS,
            pins={"analog": "A0"},
            protocol="analog",
            value_range=(0, 1023),
            unit="ppm",
            icon="🌫️",
            description="Luftqualitätssensor (CO2, NH3, NOx)"
        ),
        
        # === WASSER & FEUCHTIGKEIT ===
        "WATER_LEVEL": SensorDefinition(
            id="WATER_LEVEL",
            name="Wasserstand-Sensor",
            sensor_type=SensorType.WATER,
            pins={"analog": "A0"},
            protocol="analog",
            value_range=(0, 1023),
            unit="Level",
            icon="💧",
            description="Misst Wasserstand"
        ),
        
        "RAIN_SENSOR": SensorDefinition(
            id="RAIN_SENSOR",
            name="Regen-Detektor",
            sensor_type=SensorType.WATER,
            pins={"analog": "A0", "digital": "D2"},
            protocol="analog",
            value_range=(0, 1023),
            unit="Intensität",
            icon="🌧️",
            description="Erkennt Regen und Nässe"
        ),
        
        "SOIL_MOISTURE": SensorDefinition(
            id="SOIL_MOISTURE",
            name="Bodenfeuchte-Sensor",
            sensor_type=SensorType.WATER,
            pins={"analog": "A0"},
            protocol="analog",
            value_range=(0, 1023),
            unit="%",
            calibration_func=lambda x: 100 - (x / 1023.0 * 100),
            icon="🌱",
            description="Misst Bodenfeuchtigkeit"
        ),
        
        # === TOUCH & INPUT ===
        "CAPACITIVE_TOUCH": SensorDefinition(
            id="CAPACITIVE_TOUCH",
            name="TTP223 Kapazitiv Touch",
            sensor_type=SensorType.TOUCH,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(0, 1),
            unit="Touch",
            icon="👆",
            description="Berührungssensor (kapazitiv)"
        ),
        
        "JOYSTICK": SensorDefinition(
            id="JOYSTICK",
            name="Analog Joystick",
            sensor_type=SensorType.ROTATION,
            pins={"x": "A0", "y": "A1", "sw": "D2"},
            protocol="analog",
            value_range=(0, 1023),
            unit="XY",
            icon="🕹️",
            description="2-Achsen Joystick mit Taster"
        ),
        
        # === FEUER & INFRAROT ===
        "FLAME_SENSOR": SensorDefinition(
            id="FLAME_SENSOR",
            name="Flammen-Detektor",
            sensor_type=SensorType.FLAME,
            pins={"digital": "D2", "analog": "A0"},
            protocol="analog",
            value_range=(0, 1023),
            unit="Intensität",
            icon="🔥",
            description="IR-Flammen-Sensor"
        ),
        
        "IR_OBSTACLE": SensorDefinition(
            id="IR_OBSTACLE",
            name="IR Hindernis-Sensor",
            sensor_type=SensorType.DISTANCE,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(0, 1),
            unit="Objekt",
            icon="🚧",
            description="Infrarot-Näherungssensor"
        ),
        
        # === SPECIAL ===
        "TILT_SWITCH": SensorDefinition(
            id="TILT_SWITCH",
            name="Neigungsschalter",
            sensor_type=SensorType.MOTION,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(0, 1),
            unit="Tilt",
            icon="⚖️",
            description="Erkennt Neigung/Kipp-Bewegungen"
        ),
        
        "REED_SWITCH": SensorDefinition(
            id="REED_SWITCH",
            name="Reed-Schalter (Magnet)",
            sensor_type=SensorType.MAGNETIC,
            pins={"data": "D2"},
            protocol="digital",
            value_range=(0, 1),
            unit="Magnet",
            icon="🔲",
            description="Magnetisch betätigter Schalter"
        ),
        
        "VIBRATION_SW420": SensorDefinition(
            id="VIBRATION_SW420",
            name="SW-420 Vibrationssensor",
            sensor_type=SensorType.MOTION,
            pins={"digital": "D2", "analog": "A0"},
            protocol="digital",
            value_range=(0, 1),
            unit="Vibration",
            icon="📳",
            description="Erschütterungssensor"
        ),
    }
    
    @classmethod
    def get_sensor(cls, sensor_id: str) -> Optional[SensorDefinition]:
        """Ruft Sensor-Definition ab"""
        return cls.SENSORS.get(sensor_id)
    
    @classmethod
    def get_sensors_by_type(cls, sensor_type: SensorType) -> Dict[str, SensorDefinition]:
        """Filtert Sensoren nach Typ"""
        return {
            sid: sensor for sid, sensor in cls.SENSORS.items()
            if sensor.sensor_type == sensor_type
        }
    
    @classmethod
    def get_all_types(cls) -> list:
        """Gibt alle verfügbaren Sensor-Typen zurück"""
        return list(set(sensor.sensor_type for sensor in cls.SENSORS.values()))


# === VERWENDUNGSBEISPIEL ===
if __name__ == "__main__":
    # Alle Temperatursensoren anzeigen
    temp_sensors = SensorLibrary.get_sensors_by_type(SensorType.TEMPERATURE)
    print("🌡️ Temperatursensoren:")
    for sid, sensor in temp_sensors.items():
        print(f"  {sensor.icon} {sensor.name} ({sensor.value_range[0]}-{sensor.value_range[1]} {sensor.unit})")
    
    # Einen spezifischen Sensor abrufen
    ultrasonic = SensorLibrary.get_sensor("HC_SR04")
    if ultrasonic:
        print(f"\n📏 {ultrasonic.name}")
        print(f"   Pins: {ultrasonic.pins}")
        print(f"   Bereich: {ultrasonic.value_range} {ultrasonic.unit}")
