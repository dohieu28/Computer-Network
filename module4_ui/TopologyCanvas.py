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

        self.nodes = []
        self.links = []

        self.node_positions = {}
        self.node_status = {}

        self.dragging_node = None

        # Đổi thành list để animate nhiều packets đồng thời
        # [{"source": s, "destination": d, "progress": 0}, ...]
        self.animating_packets = []

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)

        self.highlighted_path = []

    def set_topology(self, nodes, links):
        self.nodes = self.normalize_nodes(nodes)
        self.links = self.normalize_links(links)

        for node_id in self.nodes:
            if node_id not in self.node_positions:
                self.node_positions[node_id] = (
                    random.randint(120, 750),
                    random.randint(80, 260),
                )

            if node_id not in self.node_status:
                self.node_status[node_id] = "Running"

        current_nodes = set(self.nodes)

        self.node_positions = {
            node_id: pos
            for node_id, pos in self.node_positions.items()
            if node_id in current_nodes
        }

        self.node_status = {
            node_id: status
            for node_id, status in self.node_status.items()
            if node_id in current_nodes
        }

        self.update()

    def normalize_nodes(self, nodes):
        if isinstance(nodes, dict):
            nodes = list(nodes.values())

        result = []

        for node in nodes:
            if isinstance(node, str):
                result.append(node)
            elif hasattr(node, "node_id"):
                result.append(node.node_id)
            elif isinstance(node, dict):
                result.append(node.get("node_id"))
            else:
                result.append(str(node))

        return [node_id for node_id in result if node_id]

    def normalize_links(self, links):
        result = []

        for link in links:
            if isinstance(link, tuple) and len(link) >= 2:
                source = link[0]
                target = link[1]
                status = "UP"
                cost = 1

            elif isinstance(link, dict):
                source = link.get("source")
                target = link.get("target")
                cost = link.get("cost", 1)

                data = link.get("data", {})
                status = data.get("status", link.get("status", "UP"))

            elif hasattr(link, "source") and hasattr(link, "target"):
                source = link.source
                target = link.target
                cost = getattr(link, "cost", 1)

                data = getattr(link, "data", {})
                status = data.get("status", "UP")

            else:
                continue

            if source and target:
                result.append(
                    {
                        "source": source,
                        "target": target,
                        "status": status,
                        "cost": cost,
                    }
                )

        return result

    def get_nodes(self):
        return list(self.nodes)

    def get_links(self):
        return list(self.links)

    def update_link_status(self, source, target, status):
        for link in self.links:
            same = link["source"] == source and link["target"] == target
            reverse = link["source"] == target and link["target"] == source

            if same or reverse:
                link["status"] = status
                self.update()
                return True

        return False

    def find_link(self, source, target):
        for link in self.links:
            same = link["source"] == source and link["target"] == target
            reverse = link["source"] == target and link["target"] == source

            if same or reverse:
                return link

        return None

    def animate_packet(self, source, destination):
        link = self.find_link(source, destination)

        if link is None:
            return False

        if link["status"] == "DOWN":
            return False

        # Thêm packet vào danh sách animate
        self.animating_packets.append({
            "source": source,
            "destination": destination,
            "progress": 0
        })

        # Chỉ start timer nếu chưa running
        if not self.timer.isActive():
            self.timer.start(30)

        return True

    def animate_path(self, path):
        if not path or len(path) < 2:
            return False

        return self.animate_packet(path[0], path[1])

    def update_animation(self):
        # Cập nhật tất cả packets
        for packet in self.animating_packets:
            packet["progress"] += 0.03

        # Xóa packets đã hoàn thành
        self.animating_packets = [
            p for p in self.animating_packets if p["progress"] < 1]

        # Dừng timer nếu không còn packets
        if not self.animating_packets:
            self.timer.stop()

        self.update()

    def clear_view(self):
        self.nodes.clear()
        self.links.clear()
        self.node_positions.clear()
        self.node_status.clear()

        self.dragging_node = None
        self.animating_packets.clear()

        self.timer.stop()
        self.update()

    def mousePressEvent(self, event):
        x_click = event.x()
        y_click = event.y()

        if event.button() == Qt.LeftButton:
            for node_id, (x, y) in self.node_positions.items():
                distance = math.sqrt((x_click - x) ** 2 + (y_click - y) ** 2)

                if distance <= 25:
                    self.dragging_node = node_id
                    return

        if event.button() == Qt.RightButton:
            for node_id, (x, y) in self.node_positions.items():
                distance = math.sqrt((x_click - x) ** 2 + (y_click - y) ** 2)

                if distance <= 25:
                    self.router_clicked.emit(node_id)
                    return

            for link in self.links:
                source = link["source"]
                target = link["target"]

                if source not in self.node_positions or target not in self.node_positions:
                    continue

                x1, y1 = self.node_positions[source]
                x2, y2 = self.node_positions[target]

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

    def mouseMoveEvent(self, event):
        if self.dragging_node is not None:
            self.node_positions[self.dragging_node] = (event.x(), event.y())
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_node = None

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
            source = link["source"]
            target = link["target"]

            if source not in self.node_positions or target not in self.node_positions:
                continue

            x1, y1 = self.node_positions[source]
            x2, y2 = self.node_positions[target]

            # if link["status"] == "UP":
            #     painter.setPen(QPen(Qt.black, 2))
            # else:
            #     painter.setPen(QPen(Qt.red, 4))

            is_highlighted = False

            if len(self.highlighted_path) >= 2:

                for i in range(len(self.highlighted_path) - 1):

                    a = self.highlighted_path[i]
                    b = self.highlighted_path[i + 1]

                    if (
                        (source == a and target == b)
                        or (source == b and target == a)
                    ):
                        is_highlighted = True
                        break

            if link["status"] == "DOWN":
                painter.setPen(QPen(Qt.red, 4))

            elif is_highlighted:
                painter.setPen(QPen(Qt.green, 5))

            else:
                painter.setPen(QPen(Qt.black, 2))

            painter.drawLine(x1, y1, x2, y2)

            mid_x = int((x1 + x2) / 2)
            mid_y = int((y1 + y2) / 2)

            painter.drawText(
                mid_x + 5,
                mid_y - 5,
                f"{link['status']} / cost={link['cost']}",
            )

        # Vẽ tất cả packets đang animate
        painter.setPen(QPen(Qt.blue, 2))
        painter.setBrush(QBrush(Qt.blue))
        for packet in self.animating_packets:
            source = packet["source"]
            destination = packet["destination"]
            progress = packet["progress"]

            if source not in self.node_positions or destination not in self.node_positions:
                continue

            x1, y1 = self.node_positions[source]
            x2, y2 = self.node_positions[destination]

            packet_x = x1 + (x2 - x1) * progress
            packet_y = y1 + (y2 - y1) * progress

            painter.drawEllipse(int(packet_x) - 6, int(packet_y) - 6, 12, 12)

        painter.setPen(QPen(Qt.black, 2))

        for node_id, (x, y) in self.node_positions.items():
            painter.setBrush(QBrush(Qt.white))
            painter.drawEllipse(x - 25, y - 25, 50, 50)
            painter.drawText(x - 10, y + 5, node_id)

    def highlight_path(self, path):

        self.highlighted_path = path

        self.update()

    def clear_highlight(self):
        self.highlighted_path = []
        self.update()
