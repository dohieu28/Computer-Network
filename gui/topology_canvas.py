from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, pyqtSignal
import math


class TopologyCanvas(QWidget):

    router_clicked = pyqtSignal(str)
    link_clicked = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(260)

        self.routers = []
        self.router_positions = {}
        self.links = []

    def add_router(self, router_id):
        self.routers.append(router_id)

        x = 100 + len(self.routers) * 120
        y = 120

        self.router_positions[router_id] = (x, y)
        self.update()

    def add_link(self, router_a, router_b):
        self.links.append(
            {
                "router_a": router_a,
                "router_b": router_b,
                "status": "UP"
            }
        )
        self.update()

    def toggle_link(self):
        if len(self.links) == 0:
            return

        if self.links[0]["status"] == "UP":
            self.links[0]["status"] = "DOWN"
        else:
            self.links[0]["status"] = "UP"

        self.update()

    def mousePressEvent(self, event):
        x_click = event.x()
        y_click = event.y()

        # Kiểm tra click vào router
        for router_id, (x, y) in self.router_positions.items():
            distance = math.sqrt((x_click - x) ** 2 + (y_click - y) ** 2)

            if distance <= 25:
                self.router_clicked.emit(router_id)
                return

        # Kiểm tra click vào link
        for link in self.links:
            r1 = link["router_a"]
            r2 = link["router_b"]

            x1, y1 = self.router_positions[r1]
            x2, y2 = self.router_positions[r2]

            distance = self.distance_to_line(
                x_click,
                y_click,
                x1,
                y1,
                x2,
                y2
            )

            if distance <= 8:
                self.link_clicked.emit(link)
                return

    def distance_to_line(self, px, py, x1, y1, x2, y2):
        line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        if line_length == 0:
            return 9999

        distance = abs(
            (y2 - y1) * px
            - (x2 - x1) * py
            + x2 * y1
            - y2 * x1
        ) / line_length

        return distance

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

        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(Qt.white))

        for router_id, (x, y) in self.router_positions.items():
            painter.drawEllipse(x - 25, y - 25, 50, 50)
            painter.drawText(x - 10, y + 5, router_id)