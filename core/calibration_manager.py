# -*- coding: utf-8 -*-
"""
core/calibration_manager.py
Kalibrierungs-Manager für Sensoren mit Offset/Faktor-Korrektur und Multi-Point-Kalibrierung
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


def _parse_timestamp(timestamp_str: str) -> datetime:
    """Robustes Parsing von Zeitstempeln (ISO und deutsches Format)"""
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        try:
            return datetime.strptime(timestamp_str, '%d.%m.%Y %H:%M:%S')
        except ValueError:
            return datetime.strptime(timestamp_str, '%d.%m.%Y %H:%M')


class CalibrationData:
    """Repräsentiert Kalibrierungsdaten für einen Sensor"""

    def __init__(
        self,
        sensor_id: str,
        calibration_type: str = "offset_factor",  # "offset_factor", "two_point", "multi_point"
        offset: float = 0.0,
        factor: float = 1.0,
        reference_points: Optional[List[Tuple[float, float]]] = None
    ):
        self.sensor_id = sensor_id
        self.calibration_type = calibration_type
        self.offset = offset
        self.factor = factor
        self.reference_points = reference_points or []  # [(measured, reference), ...]
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()
        self.quality_score = 0.0  # R² für Multi-Point
        self.is_active = True

    def apply(self, raw_value: float) -> float:
        """
        Wendet Kalibrierung auf Rohwert an

        Args:
            raw_value: Ungekalibrierter Sensorwert

        Returns:
            Kalibrierter Wert
        """
        if not self.is_active:
            return raw_value

        if self.calibration_type == "offset_factor":
            # Einfache Formel: calibrated = (raw + offset) * factor
            return (raw_value + self.offset) * self.factor

        elif self.calibration_type == "two_point":
            # 2-Punkt-Kalibrierung (linear interpolation)
            if len(self.reference_points) < 2:
                return raw_value

            # Sortiere Punkte nach gemessenem Wert
            points = sorted(self.reference_points, key=lambda p: p[0])
            measured1, reference1 = points[0]
            measured2, reference2 = points[1]

            # Lineare Interpolation
            if measured2 != measured1:
                slope = (reference2 - reference1) / (measured2 - measured1)
                return reference1 + slope * (raw_value - measured1)
            else:
                return raw_value

        elif self.calibration_type == "multi_point":
            # Multi-Point-Kalibrierung (Polynom-Fit)
            if len(self.reference_points) < 2:
                return raw_value

            # Extrahiere X (gemessen) und Y (referenz)
            measured_values = [p[0] for p in self.reference_points]
            reference_values = [p[1] for p in self.reference_points]

            # Fit Polynom (Grad = min(3, anzahl_punkte - 1))
            degree = min(3, len(self.reference_points) - 1)
            coeffs = np.polyfit(measured_values, reference_values, degree)
            poly = np.poly1d(coeffs)

            return float(poly(raw_value))

        return raw_value

    def calculate_quality(self) -> float:
        """
        Berechnet Qualität der Kalibrierung (R²)

        Returns:
            R² Wert (0-1, höher = besser)
        """
        if self.calibration_type == "offset_factor":
            # Kein R² für einfache Kalibrierung
            return 1.0

        if len(self.reference_points) < 2:
            return 0.0

        # Berechne R² für gegebene Punkte
        measured_values = np.array([p[0] for p in self.reference_points])
        reference_values = np.array([p[1] for p in self.reference_points])

        # Wende Kalibrierung an
        calibrated_values = np.array([self.apply(m) for m in measured_values])

        # Berechne R²
        ss_res = np.sum((reference_values - calibrated_values) ** 2)
        ss_tot = np.sum((reference_values - np.mean(reference_values)) ** 2)

        if ss_tot > 0:
            r_squared = 1 - (ss_res / ss_tot)
            self.quality_score = float(max(0, min(1, r_squared)))
        else:
            self.quality_score = 0.0

        return self.quality_score

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'sensor_id': self.sensor_id,
            'calibration_type': self.calibration_type,
            'offset': self.offset,
            'factor': self.factor,
            'reference_points': self.reference_points,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'quality_score': self.quality_score,
            'is_active': self.is_active
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CalibrationData':
        """Erstellt aus Dictionary"""
        cal = CalibrationData(
            sensor_id=data['sensor_id'],
            calibration_type=data.get('calibration_type', 'offset_factor'),
            offset=data.get('offset', 0.0),
            factor=data.get('factor', 1.0),
            reference_points=data.get('reference_points', [])
        )
        cal.created_at = data.get('created_at', datetime.now().isoformat())
        cal.modified_at = data.get('modified_at', datetime.now().isoformat())
        cal.quality_score = data.get('quality_score', 0.0)
        cal.is_active = data.get('is_active', True)
        return cal


class CalibrationManager:
    """
    Manager für Sensor-Kalibrierungen
    """

    def __init__(self, calibration_file: str = "sensor_calibrations.json"):
        self.calibration_file = calibration_file
        self.calibrations: Dict[str, CalibrationData] = {}
        self.load_calibrations()

    def load_calibrations(self) -> bool:
        """Lädt Kalibrierungen aus Datei"""
        if not os.path.exists(self.calibration_file):
            print(f"Keine Kalibrierungs-Datei gefunden: {self.calibration_file}")
            return False

        try:
            with open(self.calibration_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.calibrations = {}
            for sensor_id, cal_data in data.items():
                self.calibrations[sensor_id] = CalibrationData.from_dict(cal_data)

            print(f"✅ {len(self.calibrations)} Kalibrierungen geladen")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Laden der Kalibrierungen: {e}")
            return False

    def save_calibrations(self) -> bool:
        """Speichert Kalibrierungen in Datei"""
        try:
            data = {}
            for sensor_id, cal in self.calibrations.items():
                data[sensor_id] = cal.to_dict()

            with open(self.calibration_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✅ {len(self.calibrations)} Kalibrierungen gespeichert")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Speichern der Kalibrierungen: {e}")
            return False

    def add_calibration(self, calibration: CalibrationData) -> bool:
        """Fügt oder aktualisiert Kalibrierung hinzu"""
        calibration.modified_at = datetime.now().isoformat()
        calibration.calculate_quality()

        self.calibrations[calibration.sensor_id] = calibration
        return self.save_calibrations()

    def get_calibration(self, sensor_id: str) -> Optional[CalibrationData]:
        """Gibt Kalibrierung für Sensor zurück"""
        return self.calibrations.get(sensor_id)

    def remove_calibration(self, sensor_id: str) -> bool:
        """Entfernt Kalibrierung"""
        if sensor_id in self.calibrations:
            del self.calibrations[sensor_id]
            return self.save_calibrations()
        return False

    def apply_calibration(self, sensor_id: str, raw_value: float) -> float:
        """
        Wendet Kalibrierung auf Rohwert an

        Args:
            sensor_id: Sensor-ID
            raw_value: Ungekalibrierter Wert

        Returns:
            Kalibrierter Wert (oder Rohwert wenn keine Kalibrierung)
        """
        cal = self.get_calibration(sensor_id)
        if cal and cal.is_active:
            return cal.apply(raw_value)
        return raw_value

    def set_active(self, sensor_id: str, active: bool) -> bool:
        """Aktiviert/Deaktiviert Kalibrierung"""
        cal = self.get_calibration(sensor_id)
        if cal:
            cal.is_active = active
            cal.modified_at = datetime.now().isoformat()
            return self.save_calibrations()
        return False

    def create_offset_factor_calibration(
        self,
        sensor_id: str,
        offset: float,
        factor: float
    ) -> CalibrationData:
        """
        Erstellt einfache Offset/Faktor-Kalibrierung

        Args:
            sensor_id: Sensor-ID
            offset: Offset-Wert
            factor: Multiplikations-Faktor

        Returns:
            CalibrationData Objekt
        """
        cal = CalibrationData(
            sensor_id=sensor_id,
            calibration_type="offset_factor",
            offset=offset,
            factor=factor
        )
        self.add_calibration(cal)
        return cal

    def create_two_point_calibration(
        self,
        sensor_id: str,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> CalibrationData:
        """
        Erstellt 2-Punkt-Kalibrierung

        Args:
            sensor_id: Sensor-ID
            point1: (gemessener_wert, referenz_wert) für Punkt 1
            point2: (gemessener_wert, referenz_wert) für Punkt 2

        Returns:
            CalibrationData Objekt
        """
        cal = CalibrationData(
            sensor_id=sensor_id,
            calibration_type="two_point",
            reference_points=[point1, point2]
        )
        self.add_calibration(cal)
        return cal

    def create_multi_point_calibration(
        self,
        sensor_id: str,
        points: List[Tuple[float, float]]
    ) -> CalibrationData:
        """
        Erstellt Multi-Point-Kalibrierung

        Args:
            sensor_id: Sensor-ID
            points: Liste von (gemessener_wert, referenz_wert) Paaren

        Returns:
            CalibrationData Objekt
        """
        if len(points) < 2:
            raise ValueError("Mindestens 2 Punkte für Multi-Point-Kalibrierung benötigt")

        cal = CalibrationData(
            sensor_id=sensor_id,
            calibration_type="multi_point",
            reference_points=points
        )
        self.add_calibration(cal)
        return cal

    def auto_calibrate_two_point(
        self,
        sensor_id: str,
        measured_low: float,
        reference_low: float,
        measured_high: float,
        reference_high: float
    ) -> CalibrationData:
        """
        Automatische 2-Punkt-Kalibrierung mit Berechnung von Offset/Faktor

        Args:
            sensor_id: Sensor-ID
            measured_low: Gemessener Wert bei niedrigem Referenzwert
            reference_low: Niedriger Referenzwert
            measured_high: Gemessener Wert bei hohem Referenzwert
            reference_high: Hoher Referenzwert

        Returns:
            CalibrationData Objekt
        """
        # Berechne Offset und Faktor
        if measured_high != measured_low:
            factor = (reference_high - reference_low) / (measured_high - measured_low)
            offset = reference_low - (measured_low * factor)
        else:
            factor = 1.0
            offset = 0.0

        cal = CalibrationData(
            sensor_id=sensor_id,
            calibration_type="two_point",
            offset=offset,
            factor=factor,
            reference_points=[
                (measured_low, reference_low),
                (measured_high, reference_high)
            ]
        )
        self.add_calibration(cal)
        return cal

    def export_calibration(self, sensor_id: str, file_path: str) -> bool:
        """Exportiert einzelne Kalibrierung"""
        cal = self.get_calibration(sensor_id)
        if not cal:
            print(f"❌ Kalibrierung für '{sensor_id}' nicht gefunden")
            return False

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cal.to_dict(), f, indent=2, ensure_ascii=False)

            print(f"✅ Kalibrierung exportiert: {file_path}")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Exportieren: {e}")
            return False

    def import_calibration(self, file_path: str) -> Optional[str]:
        """
        Importiert Kalibrierung aus Datei

        Returns:
            Sensor-ID wenn erfolgreich, sonst None
        """
        if not os.path.exists(file_path):
            print(f"❌ Datei nicht gefunden: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cal = CalibrationData.from_dict(data)
            self.add_calibration(cal)

            print(f"✅ Kalibrierung importiert für: {cal.sensor_id}")
            return cal.sensor_id

        except Exception as e:
            print(f"❌ Fehler beim Importieren: {e}")
            return None

    def get_calibration_summary(self, sensor_id: str) -> Dict[str, Any]:
        """
        Gibt Zusammenfassung der Kalibrierung zurück

        Returns:
            Dictionary mit Kalibrierungs-Infos
        """
        cal = self.get_calibration(sensor_id)

        if not cal:
            return {
                'sensor_id': sensor_id,
                'is_calibrated': False,
                'status': 'Nicht kalibriert'
            }

        # Formatiere Erstellungsdatum
        try:
            created = _parse_timestamp(cal.created_at).strftime("%d.%m.%Y %H:%M")
            modified = _parse_timestamp(cal.modified_at).strftime("%d.%m.%Y %H:%M")
        except (ValueError, AttributeError) as e:
            created = cal.created_at
            modified = cal.modified_at

        # Status-Text
        if not cal.is_active:
            status = "Deaktiviert"
        elif cal.quality_score >= 0.95:
            status = "Exzellent"
        elif cal.quality_score >= 0.90:
            status = "Sehr gut"
        elif cal.quality_score >= 0.80:
            status = "Gut"
        elif cal.quality_score >= 0.70:
            status = "Befriedigend"
        else:
            status = "Mangelhaft"

        return {
            'sensor_id': sensor_id,
            'is_calibrated': True,
            'is_active': cal.is_active,
            'calibration_type': cal.calibration_type,
            'quality_score': cal.quality_score,
            'status': status,
            'created_at': created,
            'modified_at': modified,
            'num_points': len(cal.reference_points),
            'offset': cal.offset,
            'factor': cal.factor
        }

    def validate_calibration(self, sensor_id: str, test_points: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Validiert Kalibrierung mit Test-Punkten

        Args:
            sensor_id: Sensor-ID
            test_points: Liste von (gemessener_wert, erwarteter_wert) Paaren

        Returns:
            Validierungs-Ergebnisse
        """
        cal = self.get_calibration(sensor_id)

        if not cal:
            return {
                'success': False,
                'message': 'Keine Kalibrierung gefunden'
            }

        if not test_points:
            return {
                'success': False,
                'message': 'Keine Test-Punkte angegeben'
            }

        # Validiere jeden Punkt
        errors = []
        relative_errors = []

        for measured, expected in test_points:
            calibrated = cal.apply(measured)
            error = abs(calibrated - expected)
            errors.append(error)

            if expected != 0:
                rel_error = (error / abs(expected)) * 100
                relative_errors.append(rel_error)

        # Statistiken
        mean_error = float(np.mean(errors))
        max_error = float(np.max(errors))
        mean_rel_error = float(np.mean(relative_errors)) if relative_errors else 0.0

        # Bewertung
        if mean_rel_error < 1:
            rating = "Exzellent"
        elif mean_rel_error < 2:
            rating = "Sehr gut"
        elif mean_rel_error < 5:
            rating = "Gut"
        elif mean_rel_error < 10:
            rating = "Befriedigend"
        else:
            rating = "Mangelhaft"

        return {
            'success': True,
            'mean_error': mean_error,
            'max_error': max_error,
            'mean_relative_error_percent': mean_rel_error,
            'rating': rating,
            'num_test_points': len(test_points)
        }
