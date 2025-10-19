from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QComboBox, QSpinBox, QGraphicsProxyWidget
from PyQt6.QtCore import QRectF, Qt, QPointF
from PyQt6.QtGui import QColor, QBrush, QPen, QPainterPath

class BaseNode(QGraphicsItem):
    """Basisklasse für alle Knoten im visuellen Editor."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.title = title
        self.width = 180
        self.height = 100
        self.color = QColor("#2D3B4A")
        self.title_color = QColor("#1B2632")
        self.ports = []
        self.hovered_port = None
        self.is_highlighted = False # NEU: Zustand für Highlighting

    def set_highlight(self, state):
        """NEU: Aktiviert oder deaktiviert das Highlighting."""
        self.is_highlighted = state
        self.update()

    def boundingRect(self):
        # Rand für Highlighting und Ports hinzufügen
        return QRectF(-8, -2, self.width + 16, self.height + 4)

    def paint(self, painter, option, widget=None):
        # NEU: Highlight-Rahmen zeichnen, wenn aktiv
        if self.is_highlighted:
            highlight_pen = QPen(QColor("#C2A447"), 4, Qt.PenStyle.SolidLine)
            painter.setPen(highlight_pen)
            painter.drawRoundedRect(QRectF(-2, 2, self.width+4, self.height-4), 12, 12)

        # Knoten-Körper
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, 10, 10)
        painter.setPen(Qt.PenStyle.NoPen) # Kein Rahmen für den Körper selbst
        painter.fillPath(path, QBrush(self.color))
        
        # Titel-Leiste
        title_path = QPainterPath()
        title_path.addRoundedRect(0, 0, self.width, 30, 10, 10)
        title_path.addRect(0, 20, self.width, 10) 
        painter.fillPath(title_path, QBrush(self.title_color))
        
        # Titel-Text
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(QRectF(10, 5, self.width - 20, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)

        # Ports
        for port in self.ports:
            port.paint(painter, self.hovered_port == port)

    def add_port(self, name, is_output, pos_y):
        # ... (Implementation unchanged)
        port = Port(self, name, is_output, pos_y)
        self.ports.append(port)
        return port


    def itemChange(self, change, value):
        # ... (Implementation unchanged)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.ports:
                for conn in port.connections:
                    conn.update_path()
        return super().itemChange(change, value)


    def mouseMoveEvent(self, event):
        # ... (Implementation unchanged)
        self.hovered_port = self.get_port_at(event.pos())
        self.update()
        super().mouseMoveEvent(event)


    def mousePressEvent(self, event):
        # ... (Implementation unchanged)
        self.hovered_port = self.get_port_at(event.pos())
        if self.hovered_port:
            return
        super().mousePressEvent(event)


    def get_port_at(self, pos):
        # ... (Implementation unchanged)
        for port in self.ports:
            if port.boundingRect().contains(pos):
                return port
        return None


    def to_dict(self):
        return {'type': self.title, 'pos': [self.x(), self.y()]}
        
    def from_dict(self, data):
        if 'pos' in data and isinstance(data['pos'], list) and len(data['pos']) == 2:
            self.setPos(data['pos'][0], data['pos'][1])

# ... (Rest der Datei: Port, StartNode, ActionNode, WaitNode - unverändert)
class Port:
    """Repräsentiert einen Ein- oder Ausgang an einem Knoten."""
    def __init__(self, node, name, is_output, pos_y):
        self.node = node
        self.name = name
        self.is_output = is_output
        self.pos_y = pos_y
        self.radius = 6
        self.connections = []

    def get_scene_pos(self):
        x = self.node.width if self.is_output else 0
        return self.node.mapToScene(x, self.pos_y)

    def boundingRect(self):
        x = self.node.width - self.radius if self.is_output else -self.radius
        return QRectF(x, self.pos_y - self.radius, self.radius * 2, self.radius * 2)

    def paint(self, painter, is_hovered):
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        
        if is_hovered:
            painter.fillPath(path, QBrush(QColor("#f39c12")))
        else:
            painter.fillPath(path, QBrush(QColor("#7f8c8d")))

class StartNode(BaseNode):
    """Der Startpunkt einer Sequenz."""
    def __init__(self):
        super().__init__("Start")
        self.color = QColor("#16a085")
        self.height = 60
        self.out_port = self.add_port("Out", True, 45)

    def to_dict(self):
        data = super().to_dict()
        data['node_type'] = 'Start'
        return data

class ActionNode(BaseNode):
    """Ein Knoten, der eine Pin-Aktion ausführt."""
    def __init__(self, parent=None):
        super().__init__("Aktion", parent)
        self.height = 150
        self.in_port = self.add_port("In", False, 45)
        self.out_port = self.add_port("Out", True, 45)

        proxy_action = QGraphicsProxyWidget(self)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["SET_HIGH", "SET_LOW"])
        proxy_action.setWidget(self.action_combo)
        proxy_action.setPos(10, 40)
        
        proxy_pin = QGraphicsProxyWidget(self)
        self.pin_combo = QComboBox()
        self.pin_combo.addItems([f"D{i}" for i in range(14)])
        proxy_pin.setWidget(self.pin_combo)
        proxy_pin.setPos(10, 75)

        proxy_wait = QGraphicsProxyWidget(self)
        self.wait_spin = QSpinBox()
        self.wait_spin.setRange(0, 10000)
        self.wait_spin.setSuffix(" ms")
        self.wait_spin.setValue(100)
        proxy_wait.setWidget(self.wait_spin)
        proxy_wait.setPos(10, 110)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'node_type': 'Action',
            'action': self.action_combo.currentText(),
            'pin': self.pin_combo.currentText(),
            'wait': self.wait_spin.value()
        })
        return data
        
    def from_dict(self, data):
        super().from_dict(data)
        self.action_combo.setCurrentText(data.get('action', 'SET_HIGH'))
        self.pin_combo.setCurrentText(data.get('pin', 'D8'))
        self.wait_spin.setValue(data.get('wait', 100))

class WaitNode(BaseNode):
    """Ein Knoten, der auf einen Pin-Zustand wartet."""
    def __init__(self, parent=None):
        super().__init__("Warten", parent)
        self.height = 180
        self.color = QColor("#34495e")
        self.in_port = self.add_port("In", False, 45)
        self.out_port = self.add_port("Out", True, 45)

        proxy_pin = QGraphicsProxyWidget(self)
        self.pin_combo = QComboBox()
        self.pin_combo.addItems([f"D{i}" for i in range(14)])
        proxy_pin.setWidget(self.pin_combo)
        proxy_pin.setPos(10, 40)

        proxy_condition = QGraphicsProxyWidget(self)
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["HIGH", "LOW"])
        proxy_condition.setWidget(self.condition_combo)
        proxy_condition.setPos(10, 75)

        proxy_timeout = QGraphicsProxyWidget(self)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 60000)
        self.timeout_spin.setSuffix(" ms")
        self.timeout_spin.setValue(5000)
        proxy_timeout.setWidget(self.timeout_spin)
        proxy_timeout.setPos(10, 110)

        info_text = QGraphicsTextItem("Timeout nach:", self)
        info_text.setDefaultTextColor(Qt.GlobalColor.white)
        info_text.setPos(10, 140)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'node_type': 'Wait',
            'action': 'WAIT_FOR_PIN',
            'pin': self.pin_combo.currentText(),
            'value': 1 if self.condition_combo.currentText() == "HIGH" else 0,
            'timeout': self.timeout_spin.value()
        })
        return data
        
    def from_dict(self, data):
        super().from_dict(data)
        self.pin_combo.setCurrentText(data.get('pin', 'D2'))
        condition = "HIGH" if data.get('value', 1) == 1 else "LOW"
        self.condition_combo.setCurrentText(condition)
        self.timeout_spin.setValue(data.get('timeout', 5000))
