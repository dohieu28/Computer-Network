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
    QMessageBox
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("OSPF/RIP Network Emulator")
        self.resize(1100, 800)

        self.canvas = TopologyCanvas()
        self.sniffer = PacketSniffer()

        self.btn_add_router = QPushButton("Add Router")
        self.btn_add_link = QPushButton("Add Link")
        self.btn_toggle_link = QPushButton("Toggle Link Up/Down")
        self.btn_start = QPushButton("Start Simulation")

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

        self.btn_add_router.clicked.connect(self.add_router_demo)
        self.btn_add_link.clicked.connect(self.add_link_demo)
        self.btn_toggle_link.clicked.connect(self.canvas.toggle_link)
        self.btn_start.clicked.connect(self.start_demo)

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

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_add_router)
        button_layout.addWidget(self.btn_add_link)
        button_layout.addWidget(self.btn_toggle_link)
        button_layout.addWidget(self.btn_start)

        main_layout.addLayout(table_layout)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)

    def add_router_demo(self):
        router_id = f"R{len(self.canvas.routers) + 1}"
        self.canvas.add_router(router_id)

    def add_link_demo(self):
        if len(self.canvas.routers) >= 2:
            r1 = self.canvas.routers[-2]
            r2 = self.canvas.routers[-1]
            self.canvas.add_link(r1, r2)

    def start_demo(self):
        self.routing_table.setRowCount(1)

        self.routing_table.setItem(0, 0, QTableWidgetItem("192.168.1.0/24"))
        self.routing_table.setItem(0, 1, QTableWidgetItem("R2"))
        self.routing_table.setItem(0, 2, QTableWidgetItem("1"))
        self.routing_table.setItem(0, 3, QTableWidgetItem("eth0"))

        packet_info = self.sniffer.analyze_packet(
            "RIP UPDATE PACKET",
            "R1",
            "R2"
        )

        row = self.sniffer_table.rowCount()
        self.sniffer_table.insertRow(row)

        self.sniffer_table.setItem(row, 0, QTableWidgetItem(packet_info["time"]))
        self.sniffer_table.setItem(row, 1, QTableWidgetItem(packet_info["source"]))
        self.sniffer_table.setItem(row, 2, QTableWidgetItem(packet_info["destination"]))
        self.sniffer_table.setItem(row, 3, QTableWidgetItem(packet_info["protocol"]))
        self.sniffer_table.setItem(row, 4, QTableWidgetItem(str(packet_info["length"])))

    def show_router_info(self, router_id):
        QMessageBox.information(
            self,
            "Router Information",
            f"Router ID: {router_id}\n"
            f"Status: Running\n"
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