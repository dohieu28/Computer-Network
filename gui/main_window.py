from gui.topology_canvas import TopologyCanvas
from gui.packet_sniffer import PacketSniffer

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QFileDialog
)

from pathlib import Path


try:
    from core.topology_manager import TopologyManager
except ImportError:
    try:
        from core import TopologyManager
    except ImportError:
        TopologyManager = None


class SimpleTopologyManager:
    """
    Fallback tạm thời để Module 4 vẫn chạy được
    khi chưa merge được Module 1.
    Khi ghép thật, bỏ class này và dùng TopologyManager của Module 1.
    """

    def __init__(self):
        self.nodes = {}
        self.links = []

    def add_node(self, node_id, node_type="router", **data):
        self.nodes[node_id] = {
            "node_id": node_id,
            "node_type": node_type,
            "data": data
        }

    def add_link(self, source, target, cost=1, **data):
        self.links.append(
            {
                "source": source,
                "target": target,
                "cost": cost,
                "data": data
            }
        )

    def remove_node(self, node_id):
        self.nodes.pop(node_id, None)
        self.links = [
            link for link in self.links
            if link["source"] != node_id and link["target"] != node_id
        ]

    def remove_link(self, source, target):
        self.links = [
            link for link in self.links
            if not (
                (link["source"] == source and link["target"] == target)
                or
                (link["source"] == target and link["target"] == source)
            )
        ]

    def export_topology(self, json_file):
        import json

        payload = {
            "nodes": list(self.nodes.values()),
            "links": self.links
        }

        Path(json_file).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def load_topology(self, json_file):
        import json

        payload = json.loads(
            Path(json_file).read_text(encoding="utf-8")
        )

        self.nodes.clear()
        self.links.clear()

        for node in payload.get("nodes", []):
            self.nodes[node["node_id"]] = node

        self.links = payload.get("links", [])


class MainWindow(QMainWindow):

    def __init__(self, topology_manager=None):
        super().__init__()

        self.setWindowTitle("OSPF/RIP Network Emulator")
        self.resize(1200, 850)

        if topology_manager is not None:
            self.topology_manager = topology_manager
        elif TopologyManager is not None:
            self.topology_manager = TopologyManager()
        else:
            self.topology_manager = SimpleTopologyManager()

        self.canvas = TopologyCanvas()
        self.sniffer = PacketSniffer()

        self.btn_add_router = QPushButton("Add Router")
        self.btn_add_link = QPushButton("Add Link")
        self.btn_delete_router = QPushButton("Delete Router")
        self.btn_delete_link = QPushButton("Delete Link")
        self.btn_toggle_link = QPushButton("Toggle Link UP/DOWN")
        self.btn_start = QPushButton("Start Simulation")
        self.btn_clear = QPushButton("Clear View")
        self.btn_save = QPushButton("Save Topology")
        self.btn_load = QPushButton("Load Topology")

        self.combo_router_a = QComboBox()
        self.combo_router_b = QComboBox()
        self.combo_router_action = QComboBox()

        self.routing_table = QTableWidget()
        self.routing_table.setColumnCount(4)
        self.routing_table.setHorizontalHeaderLabels(
            ["Destination", "Next Hop", "Metric", "Interface"]
        )

        self.sniffer_table = QTableWidget()
        self.sniffer_table.setColumnCount(5)
        self.sniffer_table.setHorizontalHeaderLabels(
            ["Time", "Source", "Destination", "Protocol", "Length"]
        )

        self.btn_add_router.clicked.connect(self.add_router_via_manager)
        self.btn_add_link.clicked.connect(self.add_link_via_manager)
        self.btn_delete_router.clicked.connect(self.delete_router_via_manager)
        self.btn_delete_link.clicked.connect(self.delete_link_via_manager)
        self.btn_toggle_link.clicked.connect(self.toggle_selected_link_view)
        self.btn_start.clicked.connect(self.start_demo)
        self.btn_clear.clicked.connect(self.clear_view)
        self.btn_save.clicked.connect(self.save_topology)
        self.btn_load.clicked.connect(self.load_topology)

        self.canvas.router_clicked.connect(self.show_router_info)
        self.canvas.link_clicked.connect(self.show_link_info)

        main_layout = QVBoxLayout()

        main_layout.addWidget(QLabel("Topology Canvas"))
        main_layout.addWidget(self.canvas)

        table_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Routing Table"))
        left_layout.addWidget(self.routing_table)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Packet Sniffer"))
        right_layout.addWidget(self.sniffer_table)

        table_layout.addLayout(left_layout)
        table_layout.addLayout(right_layout)

        link_select_layout = QHBoxLayout()
        link_select_layout.addWidget(QLabel("Router A:"))
        link_select_layout.addWidget(self.combo_router_a)
        link_select_layout.addWidget(QLabel("Router B:"))
        link_select_layout.addWidget(self.combo_router_b)
        link_select_layout.addWidget(self.btn_add_link)
        link_select_layout.addWidget(self.btn_delete_link)
        link_select_layout.addWidget(self.btn_toggle_link)

        router_action_layout = QHBoxLayout()
        router_action_layout.addWidget(QLabel("Router Action:"))
        router_action_layout.addWidget(self.combo_router_action)
        router_action_layout.addWidget(self.btn_delete_router)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_add_router)
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_clear)
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_load)

        main_layout.addLayout(table_layout)
        main_layout.addLayout(link_select_layout)
        main_layout.addLayout(router_action_layout)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)

        self.refresh_topology_view()

    def get_manager_nodes(self):
        return self.topology_manager.nodes

    def get_manager_links(self):
        return self.topology_manager.links

    def refresh_topology_view(self):
        nodes = self.get_manager_nodes()
        links = self.get_manager_links()

        self.canvas.set_topology(nodes, links)
        self.sync_router_combo()

    def sync_router_combo(self):
        current_a = self.combo_router_a.currentText()
        current_b = self.combo_router_b.currentText()
        current_action = self.combo_router_action.currentText()

        self.combo_router_a.clear()
        self.combo_router_b.clear()
        self.combo_router_action.clear()

        node_ids = self.canvas.get_nodes()

        for node_id in node_ids:
            self.combo_router_a.addItem(node_id)
            self.combo_router_b.addItem(node_id)
            self.combo_router_action.addItem(node_id)

        for combo, current in [
            (self.combo_router_a, current_a),
            (self.combo_router_b, current_b),
            (self.combo_router_action, current_action)
        ]:
            index = combo.findText(current)
            if index >= 0:
                combo.setCurrentIndex(index)

    def add_router_via_manager(self):
        node_id = f"R{len(self.canvas.get_nodes()) + 1}"
        self.topology_manager.add_node(node_id, node_type="router")
        self.refresh_topology_view()

    def link_exists(self, source, target):
        for link in self.canvas.get_links():
            same_direction = link["source"] == source and link["target"] == target
            reverse_direction = link["source"] == target and link["target"] == source

            if same_direction or reverse_direction:
                return True

        return False

    def add_link_via_manager(self):
        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if not source or not target:
            QMessageBox.warning(self, "Warning", "Please add routers first.")
            return

        if source == target:
            QMessageBox.warning(self, "Warning", "Router A and B must be different.")
            return

        if self.link_exists(source, target):
            QMessageBox.warning(self, "Warning", "Link already exists.")
            return

        self.topology_manager.add_link(source, target, cost=1, status="UP")
        self.refresh_topology_view()

    def delete_router_via_manager(self):
        node_id = self.combo_router_action.currentText()

        if not node_id:
            QMessageBox.warning(self, "Warning", "Please select a router.")
            return

        self.topology_manager.remove_node(node_id)
        self.refresh_topology_view()

    def delete_link_via_manager(self):
        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if not source or not target:
            QMessageBox.warning(self, "Warning", "Please select two routers.")
            return

        self.topology_manager.remove_link(source, target)
        self.refresh_topology_view()

    def toggle_selected_link_view(self):
        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if not source or not target:
            QMessageBox.warning(self, "Warning", "Please select two routers.")
            return

        link = self.canvas.find_link(source, target)

        if link is None:
            QMessageBox.warning(self, "Warning", "This link does not exist.")
            return

        new_status = "DOWN" if link["status"] == "UP" else "UP"

        # Chỉ update view. Sau này nếu Module 1 có set_status thì gọi tại đây.
        self.canvas.update_link_status(source, target, new_status)

    def start_demo(self):
        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if not source or not target:
            QMessageBox.warning(self, "Warning", "Please select two routers.")
            return

        if source == target:
            QMessageBox.warning(self, "Warning", "Router A and B must be different.")
            return

        if not self.canvas.animate_packet(source, target):
            QMessageBox.warning(
                self,
                "Warning",
                "Cannot send packet. Link is missing or DOWN."
            )
            return

        self.routing_table.setRowCount(1)
        self.routing_table.setItem(0, 0, QTableWidgetItem("192.168.1.0/24"))
        self.routing_table.setItem(0, 1, QTableWidgetItem(target))
        self.routing_table.setItem(0, 2, QTableWidgetItem("1"))
        self.routing_table.setItem(0, 3, QTableWidgetItem("eth0"))

        packet_info = self.sniffer.analyze_packet(
            "RIP UPDATE PACKET",
            source,
            target
        )

        self.add_packet_log(packet_info)

    def add_packet_log(self, packet_info):
        row = self.sniffer_table.rowCount()
        self.sniffer_table.insertRow(row)

        self.sniffer_table.setItem(row, 0, QTableWidgetItem(packet_info["time"]))
        self.sniffer_table.setItem(row, 1, QTableWidgetItem(packet_info["source"]))
        self.sniffer_table.setItem(row, 2, QTableWidgetItem(packet_info["destination"]))
        self.sniffer_table.setItem(row, 3, QTableWidgetItem(packet_info["protocol"]))
        self.sniffer_table.setItem(row, 4, QTableWidgetItem(str(packet_info["length"])))

    def clear_view(self):
        self.canvas.clear_view()

        self.combo_router_a.clear()
        self.combo_router_b.clear()
        self.combo_router_action.clear()

        self.routing_table.setRowCount(0)
        self.sniffer_table.setRowCount(0)
        self.sniffer.captured_packets.clear()

    def save_topology(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Topology",
            "",
            "JSON Files (*.json)"
        )

        if not filename:
            return

        self.topology_manager.export_topology(filename)

    def load_topology(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Topology",
            "",
            "JSON Files (*.json)"
        )

        if not filename:
            return

        self.topology_manager.load_topology(filename)
        self.refresh_topology_view()

    def show_router_info(self, node_id):
        QMessageBox.information(
            self,
            "Router Information",
            f"Router ID: {node_id}\n"
            f"Role: Displayed from TopologyManager\n"
            f"Status: {self.canvas.node_status.get(node_id, 'Running')}"
        )

    def show_link_info(self, link):
        QMessageBox.information(
            self,
            "Link Information",
            f"Source: {link['source']}\n"
            f"Target: {link['target']}\n"
            f"Status: {link['status']}\n"
            f"Cost: {link['cost']}"
        )