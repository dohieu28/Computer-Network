from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import math
import random


class TopologyCanvas(QWidget):
    router_clicked = pyqtSignal(str)
    link_clicked = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(320)

        self.routers = []
        self.router_positions = {}
        self.router_status = {}
        self.links = []

        self.dragging_router = None

        self.animating = False
        self.packet_source = None
        self.packet_destination = None
        self.animation_progress = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)

    def add_router(self, router_id):
        self.routers.append(router_id)
        self.router_status[router_id] = "Running"

        x = random.randint(120, 700)
        y = random.randint(80, 250)
        self.router_positions[router_id] = (x, y)

        self.update()

    def add_link(self, router_a, router_b):
        for link in self.links:
            if (
                link["router_a"] == router_a and link["router_b"] == router_b
            ) or (
                link["router_a"] == router_b and link["router_b"] == router_a
            ):
                return False

        self.links.append({
            "router_a": router_a,
            "router_b": router_b,
            "status": "UP"
        })
        self.update()
        return True

    def delete_router(self, router_id):
        if router_id not in self.routers:
            return False

        self.routers.remove(router_id)
        self.router_positions.pop(router_id, None)
        self.router_status.pop(router_id, None)

        self.links = [
            link for link in self.links
            if link["router_a"] != router_id and link["router_b"] != router_id
        ]

        self.update()
        return True

    def delete_link(self, router_a, router_b):
        for link in self.links:
            if (
                link["router_a"] == router_a and link["router_b"] == router_b
            ) or (
                link["router_a"] == router_b and link["router_b"] == router_a
            ):
                self.links.remove(link)
                self.update()
                return True

        return False

    def rename_router(self, old_name, new_name):
        if old_name not in self.routers:
            return False

        if new_name in self.routers:
            return False

        index = self.routers.index(old_name)
        self.routers[index] = new_name

        self.router_positions[new_name] = self.router_positions.pop(old_name)
        self.router_status[new_name] = self.router_status.pop(old_name)

        for link in self.links:
            if link["router_a"] == old_name:
                link["router_a"] = new_name
            if link["router_b"] == old_name:
                link["router_b"] = new_name

        self.update()
        return True

    def toggle_router_status(self, router_id):
        if router_id not in self.router_status:
            return False

        if self.router_status[router_id] == "Running":
            self.router_status[router_id] = "Stopped"
        else:
            self.router_status[router_id] = "Running"

        self.update()
        return True

    def toggle_link(self, router_a, router_b):
        for link in self.links:
            if (
                link["router_a"] == router_a and link["router_b"] == router_b
            ) or (
                link["router_a"] == router_b and link["router_b"] == router_a
            ):
                link["status"] = "DOWN" if link["status"] == "UP" else "UP"
                self.update()
                return True

        return False

    def find_link(self, router_a, router_b):
        for link in self.links:
            if (
                link["router_a"] == router_a and link["router_b"] == router_b
            ) or (
                link["router_a"] == router_b and link["router_b"] == router_a
            ):
                return link

        return None

    def animate_packet(self, source, destination):
        link = self.find_link(source, destination)

        if link is None:
            return False

        if link["status"] == "DOWN":
            return False

        if self.router_status.get(source) == "Stopped":
            return False

        if self.router_status.get(destination) == "Stopped":
            return False

        self.packet_source = source
        self.packet_destination = destination
        self.animation_progress = 0
        self.animating = True
        self.timer.start(30)
        return True

    def update_animation(self):
        self.animation_progress += 0.03

        if self.animation_progress >= 1:
            self.animation_progress = 1
            self.animating = False
            self.timer.stop()

        self.update()

    def export_data(self):
        return {
            "routers": self.routers,
            "router_positions": self.router_positions,
            "router_status": self.router_status,
            "links": self.links
        }

    def load_data(self, data):
        self.routers = data.get("routers", [])
        self.router_positions = {
            key: tuple(value)
            for key, value in data.get("router_positions", {}).items()
        }
        self.router_status = data.get("router_status", {})
        self.links = data.get("links", [])

        self.update()

    def clear_topology(self):
        self.routers.clear()
        self.router_positions.clear()
        self.router_status.clear()
        self.links.clear()

        self.dragging_router = None
        self.animating = False
        self.packet_source = None
        self.packet_destination = None
        self.animation_progress = 0

        self.timer.stop()
        self.update()

    def mousePressEvent(self, event):
        x_click = event.x()
        y_click = event.y()

        if event.button() == Qt.LeftButton:
            for router_id, (x, y) in self.router_positions.items():
                distance = math.sqrt((x_click - x) ** 2 + (y_click - y) ** 2)

                if distance <= 25:
                    self.dragging_router = router_id
                    return

        if event.button() == Qt.RightButton:
            for router_id, (x, y) in self.router_positions.items():
                distance = math.sqrt((x_click - x) ** 2 + (y_click - y) ** 2)

                if distance <= 25:
                    self.router_clicked.emit(router_id)
                    return

            for link in self.links:
                r1 = link["router_a"]
                r2 = link["router_b"]
                x1, y1 = self.router_positions[r1]
                x2, y2 = self.router_positions[r2]

                distance = self.distance_to_line(x_click, y_click, x1, y1, x2, y2)

                if distance <= 8:
                    self.link_clicked.emit(link)
                    return

    def mouseMoveEvent(self, event):
        if self.dragging_router is not None:
            self.router_positions[self.dragging_router] = (event.x(), event.y())
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_router = None

    def distance_to_line(self, px, py, x1, y1, x2, y2):
        line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        if line_length == 0:
            return 9999

        return abs(
            (y2 - y1) * px
            - (x2 - x1) * py
            + x2 * y1
            - y2 * x1
        ) / line_length

    def paintEvent(self, event):
        painter = QPainter(self)

        for link in self.links:
            r1 = link["router_a"]
            r2 = link["router_b"]

            x1, y1 = self.router_positions[r1]
            x2, y2 = self.router_positions[r2]

            if link["status"] == "UP":
                painter.setPen(QPen(Qt.black, 2))
            else:
                painter.setPen(QPen(Qt.red, 4))

            painter.drawLine(x1, y1, x2, y2)

            mid_x = int((x1 + x2) / 2)
            mid_y = int((y1 + y2) / 2)
            painter.drawText(mid_x + 5, mid_y - 5, link["status"])

        if self.animating:
            x1, y1 = self.router_positions[self.packet_source]
            x2, y2 = self.router_positions[self.packet_destination]

            packet_x = x1 + (x2 - x1) * self.animation_progress
            packet_y = y1 + (y2 - y1) * self.animation_progress

            painter.setPen(QPen(Qt.blue, 2))
            painter.setBrush(QBrush(Qt.blue))
            painter.drawEllipse(int(packet_x) - 6, int(packet_y) - 6, 12, 12)

        for router_id, (x, y) in self.router_positions.items():
            status = self.router_status.get(router_id, "Running")

            if status == "Running":
                painter.setBrush(QBrush(Qt.white))
            else:
                painter.setBrush(QBrush(Qt.lightGray))

            painter.setPen(QPen(Qt.black, 2))
            painter.drawEllipse(x - 25, y - 25, 50, 50)
            painter.drawText(x - 10, y + 5, router_id)
            painter.drawText(x - 28, y + 43, status)