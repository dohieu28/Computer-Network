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


try:
    from TopologyManager import TopologyManager
except ImportError:
    try:
        from topology_manager import TopologyManager
    except ImportError:
        TopologyManager = None


class MainWindow(QMainWindow):
    def __init__(self, topology_manager=None):
        super().__init__()

        self.setWindowTitle("OSPF/RIP Network Emulator")
        self.resize(1200, 850)

        self.topology_manager = topology_manager

        if self.topology_manager is None and TopologyManager is not None:
            self.topology_manager = TopologyManager()

        self.canvas = TopologyCanvas()
        self.sniffer = PacketSniffer()

        self.btn_refresh = QPushButton("Refresh Topology")
        self.btn_add_router = QPushButton("Add Router via TopologyManager")
        self.btn_add_link = QPushButton("Add Link via TopologyManager")
        self.btn_delete_router = QPushButton("Delete Router via TopologyManager")
        self.btn_delete_link = QPushButton("Delete Link via TopologyManager")
        self.btn_toggle_link = QPushButton("Toggle Link View UP/DOWN")
        self.btn_start = QPushButton("Start Demo Packet")
        self.btn_clear = QPushButton("Clear View")
        self.btn_save = QPushButton("Save Topology via Manager")
        self.btn_load = QPushButton("Load Topology via Manager")

        self.combo_router_a = QComboBox()
        self.combo_router_b = QComboBox()
        self.combo_router_action = QComboBox()

        self.routing_table = QTableWidget()
        self.routing_table.setColumnCount(5)
        self.routing_table.setHorizontalHeaderLabels(
            ["Router", "Destination", "Next Hop", "Metric", "Interface"]
        )

        self.sniffer_table = QTableWidget()
        self.sniffer_table.setColumnCount(5)
        self.sniffer_table.setHorizontalHeaderLabels(
            ["Time", "Source", "Destination", "Protocol", "Length"]
        )

        self.btn_refresh.clicked.connect(self.refresh_topology_view)
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

        main_layout.addWidget(QLabel("Topology Canvas - View from Module 1 TopologyManager"))
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

        link_layout = QHBoxLayout()
        link_layout.addWidget(QLabel("Router A:"))
        link_layout.addWidget(self.combo_router_a)
        link_layout.addWidget(QLabel("Router B:"))
        link_layout.addWidget(self.combo_router_b)
        link_layout.addWidget(self.btn_add_link)
        link_layout.addWidget(self.btn_delete_link)
        link_layout.addWidget(self.btn_toggle_link)

        router_layout = QHBoxLayout()
        router_layout.addWidget(QLabel("Router Action:"))
        router_layout.addWidget(self.combo_router_action)
        router_layout.addWidget(self.btn_add_router)
        router_layout.addWidget(self.btn_delete_router)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_refresh)
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_clear)
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_load)

        main_layout.addLayout(table_layout)
        main_layout.addLayout(link_layout)
        main_layout.addLayout(router_layout)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)

        self.refresh_topology_view()

    def require_manager(self):
        if self.topology_manager is None:
            QMessageBox.warning(
                self,
                "Warning",
                "TopologyManager from Module 1 is not available."
            )
            return False

        return True

    def get_manager_nodes(self):
        if self.topology_manager is None:
            return {}

        return self.topology_manager.nodes

    def get_manager_links(self):
        if self.topology_manager is None:
            return []

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

        for node_id in self.canvas.get_nodes():
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
        if not self.require_manager():
            return

        node_id = f"R{len(self.canvas.get_nodes()) + 1}"

        self.topology_manager.add_node(node_id, node_type="router")
        self.refresh_topology_view()

    def link_exists(self, source, target):
        for link in self.canvas.get_links():
            same = link["source"] == source and link["target"] == target
            reverse = link["source"] == target and link["target"] == source

            if same or reverse:
                return True

        return False

    def add_link_via_manager(self):
        if not self.require_manager():
            return

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
        if not self.require_manager():
            return

        node_id = self.combo_router_action.currentText()

        if not node_id:
            QMessageBox.warning(self, "Warning", "Please select a router.")
            return

        self.topology_manager.remove_node(node_id)
        self.refresh_topology_view()

    def delete_link_via_manager(self):
        if not self.require_manager():
            return

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

        # Hiện tại đổi trạng thái ở view.
        # Sau này nếu Module 1 Link có set_status thì gọi tại đây.
        self.canvas.update_link_status(source, target, new_status)

    def start_demo(self):
        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if not source or not target:
            QMessageBox.warning(self, "Warning", "Please select two routers.")
            return

        if not self.canvas.animate_packet(source, target):
            QMessageBox.warning(
                self,
                "Warning",
                "Cannot send packet. Link is missing or DOWN."
            )
            return

        packet_info = self.sniffer.analyze_packet(
            "RIP UPDATE PACKET",
            source,
            target
        )

        self.add_packet_log(packet_info)

    def update_routing_table(self, router_id, routing_table):
        """
        Module 2 có thể gọi hàm này.

        Format từ RIP:
        {
            "10.0.0.0": {
                "metric": 1,
                "next_hop": "192.168.1.2",
                "interface": "eth0",
                "timestamp": ...
            }
        }
        """

        self.routing_table.setRowCount(0)

        for destination, info in routing_table.items():
            row = self.routing_table.rowCount()
            self.routing_table.insertRow(row)

            self.routing_table.setItem(row, 0, QTableWidgetItem(str(router_id)))
            self.routing_table.setItem(row, 1, QTableWidgetItem(str(destination)))
            self.routing_table.setItem(row, 2, QTableWidgetItem(str(info.get("next_hop", ""))))
            self.routing_table.setItem(row, 3, QTableWidgetItem(str(info.get("metric", ""))))
            self.routing_table.setItem(row, 4, QTableWidgetItem(str(info.get("interface", ""))))

    def add_packet_log(self, packet_info):
        row = self.sniffer_table.rowCount()
        self.sniffer_table.insertRow(row)

        self.sniffer_table.setItem(row, 0, QTableWidgetItem(str(packet_info["time"])))
        self.sniffer_table.setItem(row, 1, QTableWidgetItem(str(packet_info["source"])))
        self.sniffer_table.setItem(row, 2, QTableWidgetItem(str(packet_info["destination"])))
        self.sniffer_table.setItem(row, 3, QTableWidgetItem(str(packet_info["protocol"])))
        self.sniffer_table.setItem(row, 4, QTableWidgetItem(str(packet_info["length"])))

    def capture_packet_from_link(self, raw_bytes, src_interface, dst_interface, link):
        """
        Hàm này có thể đăng ký với Module 1:

            link.register_sniffer(self.capture_packet_from_link)
        """

        packet_info = self.sniffer.capture_from_link(
            raw_bytes,
            src_interface,
            dst_interface,
            link
        )

        self.add_packet_log(packet_info)

    def clear_view(self):
        self.canvas.clear_view()

        self.combo_router_a.clear()
        self.combo_router_b.clear()
        self.combo_router_action.clear()

        self.routing_table.setRowCount(0)
        self.sniffer_table.setRowCount(0)
        self.sniffer.captured_packets.clear()

    def save_topology(self):
        if not self.require_manager():
            return

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
        if not self.require_manager():
            return

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
            f"Source: Module 1 TopologyManager\n"
            f"Role: Display only"
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