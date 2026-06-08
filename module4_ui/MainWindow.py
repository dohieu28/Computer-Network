from module4_ui.TopologyCanvas import TopologyCanvas
from module4_ui.PacketSniffer import PacketSniffer
from module4_ui.RouterSignal import RouterSignal
import time
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
    QInputDialog,
    QFileDialog
)

import json


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.signals = RouterSignal()
        self.signals.router_updated.connect(self.update_routing_table)
        self.signals.packet_captured.connect(self.update_sniffer_ui)

        self.setWindowTitle("OSPF/RIP Network Emulator")
        self.resize(1200, 850)

        self.canvas = TopologyCanvas()
        self.sniffer = PacketSniffer(self.signals)

        self.btn_add_router = QPushButton("Add Router")
        self.btn_add_link = QPushButton("Add Link")
        self.btn_delete_router = QPushButton("Delete Router")
        self.btn_delete_link = QPushButton("Delete Link")
        self.btn_rename_router = QPushButton("Rename Router")
        self.btn_toggle_router = QPushButton("Toggle Router Running/Stopped")
        self.btn_toggle_link = QPushButton("Toggle Link UP/DOWN")
        self.btn_start = QPushButton("Start Simulation")
        self.btn_clear = QPushButton("Clear Simulation")
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
        # self.sniffer_table.setHorizontalHeaderLabels(
        #     ["Time", "Source", "Destination", "Protocol", "Length"]
        # )
        self.sniffer_table.setHorizontalHeaderLabels(
            ["no", "protocol", "info"])

        self.btn_add_router.clicked.connect(self.add_router_demo)
        self.btn_add_link.clicked.connect(self.add_link_selected)
        self.btn_delete_router.clicked.connect(self.delete_selected_router)
        self.btn_delete_link.clicked.connect(self.delete_selected_link)
        self.btn_rename_router.clicked.connect(self.rename_selected_router)
        self.btn_toggle_router.clicked.connect(self.toggle_selected_router)
        self.btn_toggle_link.clicked.connect(self.toggle_selected_link)
        self.btn_start.clicked.connect(self.start_demo)
        self.btn_clear.clicked.connect(self.clear_simulation)
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
        router_action_layout.addWidget(self.btn_rename_router)
        router_action_layout.addWidget(self.btn_toggle_router)

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

    def sync_router_combo(self):
        current_a = self.combo_router_a.currentText()
        current_b = self.combo_router_b.currentText()
        current_action = self.combo_router_action.currentText()

        self.combo_router_a.clear()
        self.combo_router_b.clear()
        self.combo_router_action.clear()

        for router_id in self.canvas.routers:
            self.combo_router_a.addItem(router_id)
            self.combo_router_b.addItem(router_id)
            self.combo_router_action.addItem(router_id)

        for combo, current in [
            (self.combo_router_a, current_a),
            (self.combo_router_b, current_b),
            (self.combo_router_action, current_action)
        ]:
            index = combo.findText(current)
            if index >= 0:
                combo.setCurrentIndex(index)

    def add_router_demo(self):
        router_id = f"R{len(self.canvas.routers) + 1}"
        self.canvas.add_router(router_id)
        self.sync_router_combo()

    def add_link_selected(self):
        self.sync_router_combo()

        router_a = self.combo_router_a.currentText()
        router_b = self.combo_router_b.currentText()

        if not router_a or not router_b:
            QMessageBox.warning(self, "Warning", "Please add routers first.")
            return

        if router_a == router_b:
            QMessageBox.warning(
                self, "Warning", "Router A and B must be different.")
            return

        if not self.canvas.add_link(router_a, router_b):
            QMessageBox.warning(self, "Warning", "Link already exists!")

    def delete_selected_router(self):
        self.sync_router_combo()
        router_id = self.combo_router_action.currentText()

        if not router_id:
            QMessageBox.warning(self, "Warning", "Please select a router.")
            return

        self.canvas.delete_router(router_id)
        self.sync_router_combo()

    def delete_selected_link(self):
        router_a = self.combo_router_a.currentText()
        router_b = self.combo_router_b.currentText()

        if not self.canvas.delete_link(router_a, router_b):
            QMessageBox.warning(self, "Warning", "This link does not exist.")

    def rename_selected_router(self):
        self.sync_router_combo()
        old_name = self.combo_router_action.currentText()

        if not old_name:
            QMessageBox.warning(self, "Warning", "Please select a router.")
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Router",
            "Enter new router name:"
        )

        if not ok or not new_name:
            return

        if not self.canvas.rename_router(old_name, new_name):
            QMessageBox.warning(
                self, "Warning", "Invalid name or name already exists.")
            return

        self.sync_router_combo()

    def toggle_selected_router(self):
        self.sync_router_combo()
        router_id = self.combo_router_action.currentText()

        if not router_id:
            QMessageBox.warning(self, "Warning", "Please select a router.")
            return

        self.canvas.toggle_router_status(router_id)

    def toggle_selected_link(self):
        router_a = self.combo_router_a.currentText()
        router_b = self.combo_router_b.currentText()

        if not self.canvas.toggle_link(router_a, router_b):
            QMessageBox.warning(self, "Warning", "This link does not exist.")

    def start_demo(self):
        router_a = self.combo_router_a.currentText()
        router_b = self.combo_router_b.currentText()

        if not router_a or not router_b:
            QMessageBox.warning(self, "Warning", "Please select two routers.")
            return

        if router_a == router_b:
            QMessageBox.warning(
                self, "Warning", "Router A and B must be different.")
            return

        if not self.canvas.animate_packet(router_a, router_b):
            QMessageBox.warning(
                self,
                "Warning",
                "Cannot send packet. Link is missing, DOWN, or router is Stopped."
            )
            return

        self.routing_table.setRowCount(1)
        self.routing_table.setItem(0, 0, QTableWidgetItem("192.168.1.0/24"))
        self.routing_table.setItem(0, 1, QTableWidgetItem(router_b))
        self.routing_table.setItem(0, 2, QTableWidgetItem("1"))
        self.routing_table.setItem(0, 3, QTableWidgetItem("eth0"))

        packet_info = self.sniffer.analyze_bytes(
            "RIP UPDATE PACKET",
            router_a,
            router_b
        )

        row = self.sniffer_table.rowCount()
        self.sniffer_table.insertRow(row)

        self.sniffer_table.setItem(
            row, 0, QTableWidgetItem(packet_info["time"]))
        self.sniffer_table.setItem(
            row, 1, QTableWidgetItem(packet_info["source"]))
        self.sniffer_table.setItem(
            row, 2, QTableWidgetItem(packet_info["destination"]))
        self.sniffer_table.setItem(
            row, 3, QTableWidgetItem(packet_info["protocol"]))
        self.sniffer_table.setItem(
            row, 4, QTableWidgetItem(str(packet_info["length"])))

    def clear_simulation(self):
        self.canvas.clear_topology()

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

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.canvas.export_data(), file, indent=4)

    def load_topology(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Topology",
            "",
            "JSON Files (*.json)"
        )

        if not filename:
            return

        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.canvas.load_data(data)
        self.sync_router_combo()

    def show_router_info(self, router_id):
        QMessageBox.information(
            self,
            "Router Information",
            f"Router ID: {router_id}\n"
            f"Status: {self.canvas.router_status.get(router_id, 'Running')}\n"
            f"Interfaces: eth0\n"
            f"Protocol: RIP/OSPF"
        )

    def show_link_info(self, link):
        QMessageBox.information(
            self,
            "Link Information",
            f"Router A: {link['router_a']}\n"
            f"Router B: {link['router_b']}\n"
            f"Status: {link['status']}"
        )

    def update_routing_table(self, target_router_id, new_table):
        """
        Hàm này nhận tín hiệu từ Module 2/3 (RIP/OSPF Engine) và vẽ lại QTableWidget:
         - param target_router_id: Tên của router vừa gửi tín hiệu (VD: "Router_A")
         - param new_table: Dictionary chứa bảng định tuyến của router đó
        """

        # 1. Kiểm tra xem người dùng có đang "bấm chọn" xem Router này không.
        # Nếu đang xem Router B mà Router A có tín hiệu cập nhật thì ta bỏ qua (không vẽ lại).
        if self.current_selected_router != target_router_id:
            return

        # self.table_widget là đối tượng QTableWidget bạn kéo thả trong QtDesigner hoặc tạo bằng code
        table = self.table_widget

        # 2. Xóa sạch các dòng dữ liệu cũ trong bảng để vẽ lại từ đầu
        table.setRowCount(0)

        # 3. Cấu hình tiêu đề các cột (Nếu chưa cấu hình ở hàm init)
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Mạng Đích (Dest)", "Next Hop", "Metric", "Cổng (Interface)", "Trạng thái"])

        # 4. Duyệt qua từng mạng trong Dictionary để điền vào các hàng
        row_index = 0
        current_time = time.time()

        for dest_network, info in new_table.items():
            # Thêm 1 hàng mới trống vào bảng
            table.insertRow(row_index)

            # --- Cột 1: Mạng Đích (Destination Network) ---
            table.setItem(row_index, 0, QTableWidgetItem(str(dest_network)))

            # --- Cột 2: Next Hop ---
            # Nếu là mạng kết nối trực tiếp, Next Hop thường để '0.0.0.0', ta đổi text cho dễ nhìn
            next_hop_str = "Directly Connected" if info['next_hop'] == '0.0.0.0' else str(
                info['next_hop'])
            table.setItem(row_index, 1, QTableWidgetItem(next_hop_str))

            # --- Cột 3: Metric ---
            metric = info['metric']
            metric_str = "16 (Unreachable)" if metric >= 16 else str(metric)
            item_metric = QTableWidgetItem(metric_str)
            # Nếu Metric = 16, bôi đỏ chữ để người dùng dễ chú ý
            if metric >= 16:
                item_metric.setForeground(QtGui.QBrush(QtGui.QColor("red")))
            table.setItem(row_index, 2, item_metric)

            # --- Cột 4: Interface ---
            table.setItem(row_index, 3, QTableWidgetItem(
                str(info['interface'])))

            # --- Cột 5: Trạng thái (Tuổi của route) ---
            if metric == 0:
                status = "Local"
            else:
                age = int(current_time - info['timestamp'])
                status = f"Update cách đây {age}s"
            table.setItem(row_index, 4, QTableWidgetItem(status))

            row_index += 1

        # 5. Tự động giãn cột cho chữ vừa vặn
        table.resizeColumnsToContents()

    def update_sniffer_ui(self, packet_info):
        """Hàm này sẽ nhận dictionary và in ra bảng Sniffer trên màn hình"""
        print(
            f"UI đã nhận được gói tin số {packet_info['no']}: {packet_info['protocol']}")
        # Lấy self.table_sniffer ra và insertRow giống hệt cách làm với Routing Table
        row = self.sniffer_table.rowCount()
        self.sniffer_table.insertRow(row)
