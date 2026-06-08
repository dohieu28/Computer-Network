from module4_ui.TopologyCanvas import TopologyCanvas
from module4_ui.PacketSniffer import PacketSniffer
from module4_ui.RouterSignal import RouterSignal

from module1_core.TopologyManager import TopologyManager
from module1_core.Interface import Interface
from module1_core.Link import Link
from module2_rip.RIPRouter import RIPRouter

from PyQt5 import QtGui
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
    QFileDialog,
)

import time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OSPF/RIP Network Emulator")
        self.resize(1200, 850)

        self.signals = RouterSignal()
        self.signals.router_updated.connect(self.update_routing_table)
        self.signals.packet_captured.connect(self.update_sniffer_ui)

        # Module 1
        self.topology_manager = TopologyManager()

        # Module 2
        self.rip_routers = {}

        # Link thật của Module 1
        self.real_links = []

        # Module 4
        self.canvas = TopologyCanvas()
        self.sniffer = PacketSniffer(self.signals)

        self.btn_refresh = QPushButton("Refresh Topology")
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
        self.routing_table.setColumnCount(5)
        self.routing_table.setHorizontalHeaderLabels(
            ["Router", "Destination", "Next Hop", "Metric", "Interface"]
        )

        self.sniffer_table = QTableWidget()
        self.sniffer_table.setColumnCount(5)
        self.sniffer_table.setHorizontalHeaderLabels(
            ["No", "Source", "Destination", "Protocol", "Length"]
        )

        self.btn_refresh.clicked.connect(self.refresh_topology_view)
        self.btn_add_router.clicked.connect(self.add_router)
        self.btn_add_link.clicked.connect(self.add_link)
        self.btn_delete_router.clicked.connect(self.delete_router)
        self.btn_delete_link.clicked.connect(self.delete_link)
        self.btn_toggle_link.clicked.connect(self.toggle_selected_link)
        self.btn_start.clicked.connect(self.start_simulation)
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

    def refresh_topology_view(self):
        self.canvas.set_topology(
            self.topology_manager.nodes,
            self.topology_manager.links
        )
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
            (self.combo_router_action, current_action),
        ]:
            index = combo.findText(current)
            if index >= 0:
                combo.setCurrentIndex(index)

    def add_router(self):
        router_id = f"R{len(self.topology_manager.nodes) + 1}"

        self.topology_manager.add_node(router_id, node_type="router")

        router_ip = f"192.168.{len(self.rip_routers) + 1}.1"
        rip_router = RIPRouter(router_id, router_ip)

        self.rip_routers[router_id] = rip_router

        self.refresh_topology_view()

    def link_exists(self, source, target):
        for link in self.canvas.get_links():
            same = link["source"] == source and link["target"] == target
            reverse = link["source"] == target and link["target"] == source

            if same or reverse:
                return True

        return False

    def add_link(self):
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

        link_index = len(self.real_links) + 1

        source_interface = Interface(
            name=f"{source}-eth{link_index}",
            ip=f"10.0.{link_index}.1",
            mac=f"00:00:00:00:{link_index:02x}:01",
            owner_router=self.rip_routers[source]
        )

        target_interface = Interface(
            name=f"{target}-eth{link_index}",
            ip=f"10.0.{link_index}.2",
            mac=f"00:00:00:00:{link_index:02x}:02",
            owner_router=self.rip_routers[target]
        )

        real_link = Link(
            source_interface,
            target_interface,
            cost=1,
            delay=0.1
        )

        # Đăng ký sniffer của Module 4 vào Link của Module 1
        real_link.register_sniffer(
            lambda raw_bytes, s=source, t=target:
            self.capture_packet_from_link(raw_bytes, s, t)
        )

        self.real_links.append(
            {
                "source": source,
                "target": target,
                "link": real_link,
                "source_interface": source_interface,
                "target_interface": target_interface
            }
        )

        self.rip_routers[source].interfaces.append(source_interface)
        self.rip_routers[target].interfaces.append(target_interface)

        self.rip_routers[source].add_direct_route(
            f"10.0.{link_index}.0",
            source_interface.name
        )

        self.rip_routers[target].add_direct_route(
            f"10.0.{link_index}.0",
            target_interface.name
        )

        self.topology_manager.add_link(
            source,
            target,
            source_interface=source_interface.name,
            target_interface=target_interface.name,
            cost=1,
            status="UP"
        )

        self.refresh_topology_view()

    def delete_router(self):
        router_id = self.combo_router_action.currentText()

        if not router_id:
            QMessageBox.warning(self, "Warning", "Please select a router.")
            return

        self.topology_manager.remove_node(router_id)

        if router_id in self.rip_routers:
            del self.rip_routers[router_id]

        self.real_links = [
            item for item in self.real_links
            if item["source"] != router_id and item["target"] != router_id
        ]

        self.refresh_topology_view()

    def delete_link(self):
        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if not source or not target:
            QMessageBox.warning(self, "Warning", "Please select two routers.")
            return

        self.topology_manager.remove_link(source, target)

        self.real_links = [
            item for item in self.real_links
            if not (
                (item["source"] == source and item["target"] == target)
                or
                (item["source"] == target and item["target"] == source)
            )
        ]

        self.refresh_topology_view()

    def toggle_selected_link(self):
        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if not source or not target:
            QMessageBox.warning(self, "Warning", "Please select two routers.")
            return

        target_link = None

        for item in self.real_links:
            same = item["source"] == source and item["target"] == target
            reverse = item["source"] == target and item["target"] == source

            if same or reverse:
                target_link = item["link"]
                break

        if target_link is None:
            QMessageBox.warning(self, "Warning", "This link does not exist.")
            return

        new_status = "DOWN" if target_link.status == "UP" else "UP"
        target_link.set_status(new_status)

        self.canvas.update_link_status(source, target, new_status)

    def start_simulation(self):
        if len(self.rip_routers) < 2:
            QMessageBox.warning(self, "Warning", "Please add at least two routers.")
            return

        if len(self.real_links) == 0:
            QMessageBox.warning(self, "Warning", "Please add at least one link.")
            return

        # Khởi động RIP thật
        for router in self.rip_routers.values():
            if not router.running:
                router.start_rip_engine()

        # Gửi update ngay để không phải chờ 30s
        for router in self.rip_routers.values():
            router.send_update_out_all_interfaces()

        # Cập nhật bảng định tuyến thật lên GUI
        for router_id, router in self.rip_routers.items():
            self.update_routing_table(router_id, router.routing_table)

        source = self.combo_router_a.currentText()
        target = self.combo_router_b.currentText()

        if source and target:
            self.canvas.animate_packet(source, target)

    def update_routing_table(self, router_id, routing_table):
        self.routing_table.setRowCount(0)

        for destination, info in routing_table.items():
            row = self.routing_table.rowCount()
            self.routing_table.insertRow(row)

            self.routing_table.setItem(row, 0, QTableWidgetItem(str(router_id)))
            self.routing_table.setItem(row, 1, QTableWidgetItem(str(destination)))
            self.routing_table.setItem(row, 2, QTableWidgetItem(str(info.get("next_hop", ""))))

            metric = info.get("metric", "")
            metric_item = QTableWidgetItem(str(metric))

            if isinstance(metric, int) and metric >= 16:
                metric_item.setForeground(QtGui.QBrush(QtGui.QColor("red")))

            self.routing_table.setItem(row, 3, metric_item)
            self.routing_table.setItem(row, 4, QTableWidgetItem(str(info.get("interface", ""))))

        self.routing_table.resizeColumnsToContents()

    def add_packet_log(self, packet_info):
        row = self.sniffer_table.rowCount()
        self.sniffer_table.insertRow(row)

        self.sniffer_table.setItem(row, 0, QTableWidgetItem(str(packet_info["no"])))
        self.sniffer_table.setItem(row, 1, QTableWidgetItem(str(packet_info["source"])))
        self.sniffer_table.setItem(row, 2, QTableWidgetItem(str(packet_info["destination"])))
        self.sniffer_table.setItem(row, 3, QTableWidgetItem(str(packet_info["protocol"])))
        self.sniffer_table.setItem(row, 4, QTableWidgetItem(str(packet_info["length"])))

    def update_sniffer_ui(self, packet_info):
        self.add_packet_log(packet_info)

    def capture_packet_from_link(self, raw_bytes, source="Unknown", destination="Unknown"):
        packet_info = self.sniffer.analyze_packet(
            raw_bytes,
            source,
            destination
        )
        self.add_packet_log(packet_info)

    def clear_view(self):
        for router in self.rip_routers.values():
            router.running = False

        self.topology_manager = TopologyManager()
        self.rip_routers.clear()
        self.real_links.clear()

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
            "JSON Files (*.json)",
        )

        if not filename:
            return

        self.topology_manager.export_topology(filename)

    def load_topology(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Topology",
            "",
            "JSON Files (*.json)",
        )

        if not filename:
            return

        self.topology_manager.load_topology(filename)

        # Khi load JSON chỉ khôi phục topology hiển thị.
        # RIPRouter/Interface/Link thật sẽ cần tạo lại riêng nếu muốn chạy simulation thật.
        self.refresh_topology_view()

    def show_router_info(self, node_id):
        router = self.rip_routers.get(node_id)

        if router is None:
            info = "No RIPRouter object found."
        else:
            info = f"RIP Router ID: {router.router_id}\nIP: {router.ip}\nInterfaces: {len(router.interfaces)}"

        QMessageBox.information(
            self,
            "Router Information",
            info
        )

    def show_link_info(self, link):
        QMessageBox.information(
            self,
            "Link Information",
            f"Source: {link['source']}\n"
            f"Target: {link['target']}\n"
            f"Status: {link['status']}\n"
            f"Cost: {link['cost']}",
        )