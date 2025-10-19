from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor, QPainterPath

class Connection(QGraphicsPathItem):
    """Eine Verbindungslinie zwischen zwei Knoten im visuellen Editor."""
    def __init__(self, start_port, end_port, parent=None):
        super().__init__(parent)
        self.start_port = start_port
        self.end_port = end_port
        
        # KORREKTUR: Die Verbindung wird bei den Ports registriert
        self.start_port.connections.append(self)
        self.end_port.connections.append(self)
        
        self.setPen(QPen(QColor("#bdc3c7"), 2))
        self.setZValue(-1) # Immer im Hintergrund
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        start_pos = self.start_port.get_scene_pos()
        end_pos = self.end_port.get_scene_pos()
        
        path.moveTo(start_pos)
        
        # Kontrollpunkte für eine geschwungene Kurve
        dx = end_pos.x() - start_pos.x()
        ctrl1_x = start_pos.x() + dx * 0.5
        ctrl1_y = start_pos.y()
        ctrl2_x = end_pos.x() - dx * 0.5
        ctrl2_y = end_pos.y()
        
        path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, end_pos.x(), end_pos.y())
        self.setPath(path)

