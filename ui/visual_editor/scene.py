from PyQt6.QtWidgets import QGraphicsScene, QGraphicsLineItem, QMenu, QMessageBox
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QAction, QKeySequence

from .node import BaseNode, StartNode, ActionNode, WaitNode
from .connection import Connection

class VisualScene(QGraphicsScene):
    """Die Leinwand, auf der die Knoten platziert und verbunden werden."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []
        self.connections = []
        self.node_map = {} # NEU: Mapping von Index zu Knoten
        self.temp_connection_line = None

    def clear_scene(self):
        self.clear()
        self.nodes = []
        self.connections = []
        self.node_map = {}

    def add_node_at(self, node_type, pos):
        """Fügt einen Knoten an einer bestimmten Position hinzu."""
        node = self.add_node(node_type)
        if node:
            node.setPos(pos)

    def add_node(self, node_type, data=None):
        # ... (Implementation unchanged)
        node_classes = {
            'start': StartNode,
            'action': ActionNode,
            'wait': WaitNode,
        }
        NodeClass = node_classes.get(node_type.lower())
        if not NodeClass:
            return None
        
        node = NodeClass()
        
        if data:
            node.from_dict(data)

        self.addItem(node)
        self.nodes.append(node)
        return node
        
    def mousePressEvent(self, event):
        # ... (Implementation unchanged)
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        
        if event.button() == Qt.MouseButton.RightButton and isinstance(item, Connection):
            self.remove_connection(item)
            return

        if isinstance(item, BaseNode):
            port = item.get_port_at(item.mapFromScene(event.scenePos()))
            if port and port.is_output:
                self.temp_connection_line = QGraphicsLineItem()
                self.temp_connection_line.setPen(QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.DashLine))
                self.temp_connection_line.setZValue(-1)
                self.addItem(self.temp_connection_line)
                self.start_port = port
                start_pos = port.get_scene_pos()
                self.temp_connection_line.setLine(start_pos.x(), start_pos.y(), start_pos.x(), start_pos.y())
                return
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        # ... (Implementation unchanged)
        if self.temp_connection_line:
            start_pos = self.start_port.get_scene_pos()
            end_pos = event.scenePos()
            self.temp_connection_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            
            for node in self.nodes:
                port = node.get_port_at(node.mapFromScene(event.scenePos()))
                if port and not port.is_output and port.node != self.start_port.node:
                    node.hovered_port = port
                else:
                    node.hovered_port = None
                node.update()
        else:
            super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        # ... (Implementation unchanged)
        if self.temp_connection_line:
            self.removeItem(self.temp_connection_line)
            self.temp_connection_line = None
            
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            end_port = None
            if isinstance(item, BaseNode):
                end_port = item.get_port_at(item.mapFromScene(event.scenePos()))

            if self.start_port and end_port and not end_port.is_output and self.start_port.node != end_port.node:
                if self.start_port.connections:
                    for conn in self.start_port.connections[:]: 
                        self.remove_connection(conn)

                conn = Connection(self.start_port, end_port)
                self.addItem(conn)
                self.connections.append(conn)
            
            for node in self.nodes:
                node.hovered_port = None
                node.update()

        super().mouseReleaseEvent(event)

    def remove_connection(self, connection):
        if connection in self.connections: self.connections.remove(connection)
        if connection in connection.start_port.connections: connection.start_port.connections.remove(connection)
        if connection in connection.end_port.connections: connection.end_port.connections.remove(connection)
        self.removeItem(connection)

    def keyPressEvent(self, event):
        """NEU: Löschen von Knoten mit der Entf-Taste."""
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_items()
        else:
            super().keyPressEvent(event)

    def delete_selected_items(self):
        """NEU: Löscht alle ausgewählten Knoten und ihre Verbindungen."""
        for item in self.selectedItems():
            if isinstance(item, BaseNode) and not isinstance(item, StartNode):
                # Alle Verbindungen des Knotens entfernen
                for port in item.ports:
                    for conn in port.connections[:]: # Kopie der Liste, da sie modifiziert wird
                        self.remove_connection(conn)
                self.removeItem(item)
                if item in self.nodes:
                    self.nodes.remove(item)
            elif isinstance(item, Connection):
                self.remove_connection(item)

    def highlight_node(self, node_index):
        """NEU: Hebt einen Knoten hervor und entfernt die Hervorhebung bei anderen."""
        for i, node in self.node_map.items():
            is_active = (i == node_index)
            node.set_highlight(is_active)

    def load_sequence_from_data(self, sequence_data):
        """NEU: Eigene Funktion zum Laden, baut die node_map auf."""
        start_node = self.add_node(node_type='start')
        last_node = start_node
        self.node_map = {} # Reset map

        if 'steps' in sequence_data:
            for i, step in enumerate(sequence_data.get('steps', [])):
                node_type = step.get('action')
                node = None
                
                if node_type in ['SET_HIGH', 'SET_LOW']:
                    node = self.add_node('action', data=step)
                elif node_type == 'WAIT_FOR_PIN':
                    node = self.add_node('wait', data=step)
                
                if node:
                    if 'pos' not in step: 
                        node.setPos(last_node.x() + 250, last_node.y())
                    
                    self.node_map[i] = node # Mapping von Index zu Knoten für Highlighting
                    
                    conn = Connection(last_node.out_port, node.in_port)
                    self.addItem(conn)
                    self.connections.append(conn)
                    last_node = node

    def to_sequence_steps(self):
        # ... (Implementation unchanged)
        start_node = next((node for node in self.nodes if isinstance(node, StartNode)), None)
        if not start_node:
            return [], False, "Kein Start-Knoten gefunden."

        steps = []
        visited = set()
        current_node = start_node
        node_counter = 0

        while current_node:
            if current_node in visited:
                return [], False, "Endlosschleife in der Sequenz entdeckt."
            visited.add(current_node)

            if not isinstance(current_node, StartNode):
                step_data = current_node.to_dict()
                # Position für das nächste Laden speichern
                step_data['pos'] = [current_node.x(), current_node.y()]
                steps.append(step_data)
                node_counter += 1

            if not hasattr(current_node, 'out_port') or not current_node.out_port.connections:
                break
            
            next_connection = current_node.out_port.connections[0]
            current_node = next_connection.end_port.node
        
        return steps, True, "Sequenz erfolgreich gespeichert."
