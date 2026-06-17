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
    QTextEdit,
    QAbstractItemView,
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
        self.signals.timer_updated.connect(self.update_timer_display)
        self.signals.packet_sent.connect(self.animate_rip_packet)

        # Module 1
        self.topology_manager = TopologyManager()

        # Module 2
        self.rip_routers = {}

        # Link thật của Module 1
        self.real_links = []

        # Module 4
        self.canvas = TopologyCanvas()
        self.sniffer = PacketSniffer(self.signals)

        self.simulation_running = False

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

        # Combo box để chọn router xem routing table
        self.combo_router_view = QComboBox()
        self.combo_router_view.addItem("All Routers")
        self.combo_router_view.currentTextChanged.connect(
            self.on_router_view_changed)

        self.routing_table = QTableWidget()
        self.routing_table.setColumnCount(6)
        self.routing_table.setHorizontalHeaderLabels(
            ["Protocol", "Router", "Destination",
                "Next Hop", "Metric", "Interface"]
        )

        self.routing_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.routing_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.routing_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.routing_table.cellClicked.connect(self.on_route_selected)

        self.txt_next_hop_chain = QTextEdit()
        self.txt_next_hop_chain.setReadOnly(True)
        self.txt_next_hop_chain.setMaximumHeight(80)

        # Lưu lịch sử routing table cho mỗi router
        self.routing_tables_history = {}

        # Lưu lịch sử timers cho mỗi router
        self.timers_history = {}

        self.sniffer_table = QTableWidget()
        self.sniffer_table.setColumnCount(5)
        self.sniffer_table.setHorizontalHeaderLabels(
            ["No", "Source", "Destination", "Protocol", "Length"]
        )

        # Timer Table - hiển thị RIP timers
        self.timer_table = QTableWidget()
        self.timer_table.setColumnCount(8)
        self.timer_table.setHorizontalHeaderLabels(
            ["Router", "Network", "Metric", "Status", "Update Timer",
                "Invalid Timer", "Hold Down Timer", "Flush Timer"]
        )
        self.timer_table.setMaximumHeight(150)

        self.btn_refresh.clicked.connect(self.refresh_topology_view)
        self.btn_add_router.clicked.connect(self.add_router)
        self.btn_add_link.clicked.connect(self.add_link)
        self.btn_delete_router.clicked.connect(self.delete_router)
        self.btn_delete_link.clicked.connect(self.delete_link)
        self.btn_toggle_link.clicked.connect(self.toggle_selected_link)
        # self.btn_start.clicked.connect(self.start_simulation)
        # <-- Thay đổi nút Start thành Toggle Simulation
        self.btn_start.clicked.connect(self.toggle_simulation)
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

        # Thêm combo box để chọn router
        router_select_layout = QHBoxLayout()
        router_select_layout.addWidget(QLabel("Select Router:"))
        router_select_layout.addWidget(self.combo_router_view)
        router_select_layout.addStretch()
        left_layout.addLayout(router_select_layout)

        left_layout.addWidget(self.routing_table)
        left_layout.addWidget(QLabel("Best Path Next-Hop Chain:"))
        left_layout.addWidget(self.txt_next_hop_chain)

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

        # Thêm Timer Table
        main_layout.addWidget(QLabel("RIP Timers (Routes Status & Countdown)"))
        main_layout.addWidget(self.timer_table)

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
        current_view = self.combo_router_view.currentText()

        self.combo_router_a.clear()
        self.combo_router_b.clear()
        self.combo_router_action.clear()

        # Không xóa combo_router_view, chỉ cập nhật routers
        routers_list = list(self.canvas.get_nodes())

        # Cập nhật combo_router_view
        self.combo_router_view.blockSignals(True)  # Tắm tín hiệu tạm thời
        self.combo_router_view.clear()
        self.combo_router_view.addItem("All Routers")
        for router_id in routers_list:
            self.combo_router_view.addItem(router_id)

        # Khôi phục lựa chọn trước đó
        index = self.combo_router_view.findText(current_view)
        if index >= 0:
            self.combo_router_view.setCurrentIndex(index)
        self.combo_router_view.blockSignals(False)  # Bật tín hiệu lại

        for node_id in routers_list:
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

    def animate_rip_packet(self, router_id, interface_name):

        for item in self.real_links:

            if item["source_interface"].name == interface_name:

                self.canvas.animate_packet(
                    item["source"],
                    item["target"]
                )

            elif item["target_interface"].name == interface_name:

                self.canvas.animate_packet(
                    item["target"],
                    item["source"]
                )

    def add_router(self):
        router_id = f"R{len(self.topology_manager.nodes) + 1}"

        self.topology_manager.add_node(router_id, node_type="router")

        router_ip = f"192.168.{len(self.rip_routers) + 1}.1"
        rip_router = RIPRouter(router_id, router_ip, self.signals)

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
            QMessageBox.warning(
                self, "Warning", "Router A and B must be different.")
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

        for item in self.real_links:
            if item["source"] == router_id:

                self.rip_routers[item["source"]].handle_interface_down(
                    item["source_interface"].name
                )

                self.rip_routers[item["target"]].handle_interface_down(
                    item["target_interface"].name)

            elif item["target"] == router_id:

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
            QMessageBox.warning(
                self,
                "Warning",
                "Please select two routers."
            )
            return

    # Tìm link cần xóa
        link_to_remove = None

        for item in self.real_links:
            if (
                (item["source"] == source and item["target"] == target)
                or
                (item["source"] == target and item["target"] == source)
            ):
                link_to_remove = item
                break

        if link_to_remove is None:
            QMessageBox.warning(
                self,
                "Warning",
                "Link does not exist."
            )
            return

        if self.is_simulation_running():
         # Thông báo cho RIP rằng interface bị DOWN
            self.rip_routers[source].handle_interface_down(
                link_to_remove["source_interface"].name
            )

            self.rip_routers[target].handle_interface_down(
                link_to_remove["target_interface"].name
            )

        # Xóa khỏi danh sách link thật
        self.real_links.remove(link_to_remove)

        # Xóa khỏi topology hiển thị
        self.topology_manager.remove_link(source, target)

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

        if self.is_simulation_running():

            if new_status == "DOWN":
                self.rip_routers[source].handle_interface_down(
                    item["source_interface"].name
                )
                self.rip_routers[target].handle_interface_down(
                    item["target_interface"].name
                )

            else:
                # Khi bật lại link, cần thông báo cho RIP để nó có thể cập nhật routing table nếu cần
                self.rip_routers[source].handle_interface_up(
                    item["source_interface"].name
                )
                self.rip_routers[target].handle_interface_up(
                    item["target_interface"].name
                )

        self.canvas.update_link_status(source, target, new_status)

    def start_simulation(self):
        # Khởi động RIP ENGINE
        if len(self.rip_routers) < 2:
            QMessageBox.warning(
                self, "Warning", "Please add at least two routers.")
            return False

        if len(self.real_links) == 0:
            QMessageBox.warning(
                self, "Warning", "Please add at least one link.")
            return False

        # # Nếu simulation đã chạy, không làm gì cả
        # if self.start_simulation:
        #     return

        self.simulation_running = True

        # Khởi động RIP thật
        for router in self.rip_routers.values():
            if not router.running:
                router.start_rip_engine()  # <-- Khởi chạy RIP Engine thật sự

        # Cập nhật bảng định tuyến thật lên GUI
        for router_id, router in self.rip_routers.items():
            self.update_routing_table(router_id, router.routing_table)

        return True

    def stop_simulation(self):

        for router in self.rip_routers.values():
            router.running = False

        print("Simulation stopped.")

    def is_simulation_running(self):
        return self.simulation_running

    def update_routing_table(self, router_id, routing_table):
        # Lưu routing table của router này vào lịch sử
        self.routing_tables_history[router_id] = routing_table

        # Hiển thị routing table dựa trên lựa chọn combo_router_view
        self.display_routing_table()

    def display_routing_table(self):
        """Hiển thị routing table dựa trên router được chọn"""
        selected_router = self.combo_router_view.currentText()

        self.routing_table.setRowCount(0)

        if selected_router == "All Routers":
            # Hiển thị tất cả routers
            for router_id, routing_table in self.routing_tables_history.items():
                self._add_routes_to_table(router_id, routing_table)
        else:
            # Hiển thị router được chọn
            if selected_router in self.routing_tables_history:
                routing_table = self.routing_tables_history[selected_router]
                self._add_routes_to_table(selected_router, routing_table)

        self.routing_table.resizeColumnsToContents()

    def _add_routes_to_table(self, router_id, routing_table):
        """Thêm routes của một router vào bảng"""
        for destination, info in routing_table.items():
            row = self.routing_table.rowCount()
            self.routing_table.insertRow(row)

            self.routing_table.setItem(
                row, 0, QTableWidgetItem(str(info.get("protocol", "")))
            )
            self.routing_table.setItem(
                row, 1, QTableWidgetItem(str(router_id)))
            self.routing_table.setItem(
                row, 2, QTableWidgetItem(str(destination)))
            self.routing_table.setItem(
                row, 3, QTableWidgetItem(str(info.get("next_hop", ""))))

            metric = info.get("metric", "")
            metric_item = QTableWidgetItem(str(metric))

            if isinstance(metric, int) and metric >= 16:
                metric_item.setForeground(QtGui.QBrush(QtGui.QColor("red")))

            self.routing_table.setItem(row, 4, metric_item)
            self.routing_table.setItem(
                row, 5, QTableWidgetItem(str(info.get("interface", ""))))

    def display_timer_table(self):
        """Hiển thị RIP Timer theo router được chọn"""

        selected_router = self.combo_router_view.currentText()

        self.timer_table.setRowCount(0)

        if selected_router == "All Routers":
            routers_to_show = self.timers_history.items()
        else:
            if selected_router not in self.timers_history:
                return

            routers_to_show = [
                (selected_router, self.timers_history[selected_router])
            ]

        for rid, timers in routers_to_show:

            for network, info in timers.items():

                row = self.timer_table.rowCount()
                self.timer_table.insertRow(row)

                # Router
                self.timer_table.setItem(
                    row, 0,
                    QTableWidgetItem(str(rid))
                )

                # Network
                self.timer_table.setItem(
                    row, 1,
                    QTableWidgetItem(str(network))
                )

                # Metric
                metric_item = QTableWidgetItem(str(info["metric"]))
                if info["metric"] >= 16:
                    metric_item.setForeground(
                        QtGui.QBrush(QtGui.QColor("red"))
                    )
                self.timer_table.setItem(row, 2, metric_item)

                # Status
                status_item = QTableWidgetItem(info["status"])

                if info["status"] == "VALID":
                    status_item.setForeground(
                        QtGui.QBrush(QtGui.QColor("green"))
                    )

                elif info["status"] in ("INVALID", "HOLD_DOWN"):
                    status_item.setForeground(
                        QtGui.QBrush(QtGui.QColor("orange"))
                    )

                elif info["status"] == "FLUSH":
                    status_item.setForeground(
                        QtGui.QBrush(QtGui.QColor("red"))
                    )

                self.timer_table.setItem(row, 3, status_item)

                # Update Timer
                item = QTableWidgetItem(f"{info['update_timer']}s")
                self.set_timer_color(item, info['update_timer'])
                self.timer_table.setItem(row, 4, item)

                # Invalid Timer
                item = QTableWidgetItem(f"{info['invalid_timer']}s")
                self.set_timer_color(item, info['invalid_timer'])
                self.timer_table.setItem(row, 5, item)

                # Hold Down Timer
                item = QTableWidgetItem(f"{info['hold_down_timer']}s")
                self.set_timer_color(item, info['hold_down_timer'])
                self.timer_table.setItem(row, 6, item)

                # Flush Timer
                item = QTableWidgetItem(f"{info['flush_timer']}s")
                self.set_timer_color(item, info['flush_timer'])
                self.timer_table.setItem(row, 7, item)

        self.timer_table.resizeColumnsToContents()

    def on_router_view_changed(self, router_name):
        """Được gọi khi chọn router khác trong combo box"""
        self.display_routing_table()
        self.display_timer_table()

    def add_packet_log(self, packet_info):
        row = self.sniffer_table.rowCount()
        self.sniffer_table.insertRow(row)

        self.sniffer_table.setItem(
            row, 0, QTableWidgetItem(str(packet_info["no"])))
        self.sniffer_table.setItem(
            row, 1, QTableWidgetItem(str(packet_info["source"])))
        self.sniffer_table.setItem(
            row, 2, QTableWidgetItem(str(packet_info["destination"])))
        self.sniffer_table.setItem(
            row, 3, QTableWidgetItem(str(packet_info["protocol"])))
        self.sniffer_table.setItem(
            row, 4, QTableWidgetItem(str(packet_info["length"])))

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
        self.timer_table.setRowCount(0)
        self.sniffer.captured_packets.clear()
        self.routing_tables_history.clear()
        self.timers_history.clear()

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

    def set_timer_color(self, item, value):
        if isinstance(value, str):
            item.setForeground(
                QtGui.QBrush(QtGui.QColor("gray"))
            )
        elif value < 10:
            item.setForeground(
                QtGui.QBrush(QtGui.QColor("red"))
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

    def update_timer_display(self, router_id, timers_info):
        """Cập nhật timer display khi router emit signal"""
        # Lưu timers của router này vào history
        self.timers_history[router_id] = timers_info

        self.display_timer_table()  # Cập nhật hiển thị timer table dựa trên lịch sử

        self.timer_table.resizeColumnsToContents()

    def find_router_by_interface_ip(self, ip):

        for router_id, router in self.rip_routers.items():

            for interface in router.interfaces:

                if interface.ip == ip:
                    return router_id

        return None

    def highlight_best_path(self, start_router_id, destination_network):

        path = []

        current_router = start_router_id

        visited = set()

        while True:

            if current_router in visited:
                break

            visited.add(current_router)

            router = self.rip_routers[current_router]

            if destination_network not in router.routing_table:
                break

            route = router.routing_table[destination_network]

            # mạng trực tiếp
            if route["metric"] == 0:

                path.append(current_router)
                break

            next_hop_ip = route["next_hop"]

            next_router = self.find_router_by_interface_ip(next_hop_ip)

            if next_router is None:
                break

            path.append(current_router)

            current_router = next_router

        if current_router not in path:
            path.append(current_router)

        self.canvas.highlight_path(path)

    def build_next_hop_chain(self, start_router, destination_network):

        chain = []

        path = []

        current_router = start_router

        visited = set()

        while True:

            if current_router in visited:
                chain.append("LOOP DETECTED")
                break

            visited.add(current_router)

            router = self.rip_routers[current_router]

            if destination_network not in router.routing_table:
                chain.append("NO ROUTE")
                break

            route = router.routing_table[destination_network]

            path.append(current_router)

            # mạng trực tiếp
            if route["metric"] == 0:

                chain.append(
                    f"{current_router} -> Directly Connected ({destination_network})"
                )

                break

            next_hop = route["next_hop"]

            chain.append(
                f"{current_router} -> {next_hop}"
            )

            next_router = self.find_router_by_interface_ip(next_hop)

            if next_router is None:
                break

            current_router = next_router

        print(path)
        print(chain)

        return path, chain

    def on_route_selected(self, row, column):

        if column != 2:
            return

        router_id = self.routing_table.item(row, 1).text()

        destination = self.routing_table.item(row, 2).text()

        path, chain = self.build_next_hop_chain(
            router_id,
            destination
        )

        self.canvas.highlight_path(path)

        self.txt_next_hop_chain.setPlainText(
            "\n".join(chain)
        )

        print('Clicked on route:', router_id, destination)

    def toggle_simulation(self):

        if not self.simulation_running:

            if self.start_simulation():

                self.simulation_running = True
                self.btn_start.setText(
                    "Stop Simulation"
                )

        else:

            self.stop_simulation()

            self.simulation_running = False
            self.btn_start.setText(
                "Start Simulation"
            )
