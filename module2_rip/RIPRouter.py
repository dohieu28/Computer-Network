import time
import threading
import logging
import random
from scapy.all import Ether, IP, UDP, RIP, RIPEntry
from module2_rip.RIPPacketProcessor import RIPPacketProcessor
from module4_ui.RouterSignal import RouterSignal

# Cấu hình logging để debug dễ dàng trên Terminal
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

# Constants cho Timers của RIP (Có thể thu nhỏ lại để test cho nhanh, vd: 3, 18, 24)
UPDATE_TIMER = 30
INVALID_TIMER = 180
HOLD_DOWN_TIMER = 180
FLUSH_TIMER = 240
INFINITY = 16


class RIPRouter:
    """
    Lớp định tuyến RIP, kế thừa (hoặc hoạt động cùng) VirtualRouter ở Module 1
    """

    def __init__(self, router_id, router_ip=None, signals=None):
        self.router_id = router_id
        self.router_ip = router_ip
        self.signals = signals if signals else RouterSignal()
        # Danh sách các cổng mạng (Sẽ do Module 1 cung cấp)
        self.interfaces = []

        # Cấu trúc bảng định tuyến:
        # { '10.0.0.0': {'metric': 1, 'next_hop': '192.168.1.2', 'interface': 'eth0', 'timestamp': 1600000.0} }
        self.routing_table = {}
        self.last_update_time = time.time()

        self.processor = RIPPacketProcessor(self)
        self.running = False

    def add_direct_route(self, network_ip, interface_name):
        """Thêm mạng kết nối trực tiếp (Metric = 0)"""
        self.routing_table[network_ip] = {
            'protocol': 'C',  # Connected
            'metric': 0,
            'next_hop': 'DIRECT',  # Kết nối trực tiếp
            'interface': interface_name,
            # Routes trực tiếp thường không bao giờ hết hạn, cần xử lý logic riêng
            'timestamp': time.time(),
            'hold_down_until': 0
        }

    def start_rip_engine(self):
        """Khởi động tiến trình đa luồng của RIP"""
        self.running = True

        # Luồng 1: Định kỳ gửi Update mỗi 30s
        threading.Thread(target=self._periodic_update_loop,
                         daemon=True).start()

        # Luồng 2: Kiểm tra Garbage Collection (Route hết hạn)
        threading.Thread(target=self._timer_check_loop, daemon=True).start()
        logging.info(f"[{self.router_id}] Đã khởi động RIP Engine.")

    def apply_split_horizon(self, route_list, out_interface, poison_reverse=True):
        """
        Xử lý Split Horizon và Poison Reverse
        """
        processed_routes = []
        for dest, info in route_list.items():
            metric = info['metric']

            # Nếu route này được học TỪ interface chuẩn bị gửi ra
            if info['interface'] == out_interface:
                if poison_reverse:
                    metric = INFINITY  # Đánh thuốc độc
                else:
                    continue  # Bỏ qua (Split Horizon cơ bản)

            processed_routes.append({'addr': dest, 'metric': metric})

        return processed_routes

    def craft_rip_update(self, target_interface):
        """Dùng Scapy để tạo mảng byte gói tin RIPv2"""
        # Áp dụng quy tắc Split Horizon & Poison Reverse
        interface_obj = None

        for iface in self.interfaces:
            if iface.name == target_interface:
                interface_obj = iface
                break

        if not interface_obj:
            return None

        routes_to_send = self.apply_split_horizon(
            self.routing_table, target_interface, poison_reverse=True)

        if not routes_to_send:
            return None

        # Khởi tạo gói tin Multicast chuẩn RIPv2
        eth_layer = Ether(dst="01:00:5E:00:00:09")  # Multicast MAC
        # Multicast IP RIPv2
        ip_layer = IP(src=interface_obj.ip, dst="224.0.0.9")
        udp_layer = UDP(sport=520, dport=520)
        rip_header = RIP(cmd=2, version=2)  # cmd=2 là Response

        # Nối các layer lại với nhau
        packet = eth_layer / ip_layer / udp_layer / rip_header

        # Thêm từng route vào payload
        for route in routes_to_send:
            packet = packet / \
                RIPEntry(addr=route['addr'], metric=route['metric'])

        # Trả về MẢNG BYTE THÔ để Module 1 chuyển qua cáp mạng
        return bytes(packet)

    def send_update_out_all_interfaces(self):
        """Gửi Update ra tất cả các cổng (gọi Module 1 để gửi)"""
        for interface in self.interfaces:
            # Scapy đóng gói bảng định tuyến thành mảng byte
            raw_bytes = self.craft_rip_update(interface.name)
            if raw_bytes:
                # LƯU Ý: interface.send() là hàm sẽ được định nghĩa ở Module 1
                interface.send(raw_bytes)
                self.signals.packet_sent.emit(
                    self.router_id, interface.name)
                logging.debug(
                    f"[{self.router_id}] Đã gửi RIP Update ra cổng {interface.name}")

    def send_triggered_update(self):
        """Gửi ngay lập tức khi mạng có biến (Không đợi 30s)"""
        delay = random.uniform(
            1, 5)  # Delay ngẫu nhiên từ 1-5s để tránh đồng loạt
        logging.info(f"[{self.router_id}] Kích hoạt Triggered Update!")
        # self.send_update_out_all_interfaces()

        threading.Timer(delay, self.send_update_out_all_interfaces).start()

        # Bắn tín hiệu lên GUI (Module 4) ở đây
        # Example: signal_ui_update(self.router_id, self.routing_table)

    def handle_interface_down(self, interface_name):
        """
       Xử lý khi interface DOWN.

       - Tất cả route đi qua interface này đều bị Route Poisoning (metric = 16)
       - Reset timer
       - Gửi Triggered Update
       - Để _timer_check_loop() tự FLUSH sau
       """

        # poisoned_count = 0
        route_changed = False
        current_time = time.time()

        for network, info in self.routing_table.items():

            # Chỉ xử lý các route đi qua interface này
            if info["interface"] != interface_name:
                continue

            # Nếu đã unreachable rồi thì bỏ qua
            if info["metric"] >= INFINITY:
                continue

            info["metric"] = INFINITY
            # poisoned_count += 1
            info["timestamp"] = current_time

            # Nếu bạn có hold_down_until
            info["hold_down_until"] = current_time + HOLD_DOWN_TIMER

            logging.warning(
                f"[{self.router_id}] "
                f"Route {network} via {interface_name} is DOWN."
            )

            route_changed = True

        if route_changed:
            # self.signals.route_poisoned.emit(poisoned_count)
            self.send_triggered_update()

            self.signals.router_updated.emit(
                self.router_id,
                self.routing_table
            )

    def handle_interface_up(self, interface_name):
        """
       Xử lý khi một interface chuyển sang trạng thái UP.

       - Khôi phục route kết nối trực tiếp.
       - Gửi Triggered Update để các router lân cận học lại route.
       """

        interface_obj = None

        for iface in self.interfaces:
            if iface.name == interface_name:
                interface_obj = iface
                break

        if interface_obj is None:
            logging.error(
                f"[{self.router_id}] Interface {interface_name} not found.")
            return

        # Tính network từ địa chỉ IP của interface
        ip_parts = interface_obj.ip.split(".")
        network = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0"

        current_time = time.time()

        # Nếu route đã tồn tại thì chỉ cập nhật lại
        if network in self.routing_table:

            self.routing_table[network]["protocol"] = "C"
            self.routing_table[network]["metric"] = 0
            self.routing_table[network]["next_hop"] = "DIRECT"
            self.routing_table[network]["interface"] = interface_obj.name
            self.routing_table[network]["timestamp"] = current_time
            self.routing_table[network]["hold_down_until"] = 0

        else:
            self.routing_table[network] = {
                "protocol": "C",
                "metric": 0,
                "next_hop": "DIRECT",
                "interface": interface_obj.name,
                "timestamp": current_time,
                "hold_down_until": 0,
            }

        logging.info(
            f"[{self.router_id}] Direct route {network} restored on {interface_obj.name}"
        )

        # Gửi Triggered Update
        self.send_triggered_update()

        # Cập nhật GUI
        self.signals.router_updated.emit(
            self.router_id,
            self.routing_table
        )

    def _periodic_update_loop(self):
        """Luồng đếm ngược 30s"""
        while self.running:
            self.send_update_out_all_interfaces()
            self.last_update_time = time.time()

            end_time = self.last_update_time + UPDATE_TIMER
            while self.running and time.time() < end_time:
                time.sleep(0.1)

    def _timer_check_loop(self):
        """Kiểm tra Invalid / Hold-down / Flush Timer"""

        while self.running:

            current_time = time.time()
            update_remaining = max(
                0, UPDATE_TIMER - (current_time - self.last_update_time))
            routes_to_delete = []
            route_changed = False

            timers_info = {}

            for dest, info in list(self.routing_table.items()):

                # ==========================
                # DIRECT ROUTE
                # ==========================
                if info.get("protocol") == "C" or info["metric"] == 0:

                    timers_info[dest] = {
                        "metric": info["metric"],
                        "status": "DIRECT",
                        "update_timer": round(update_remaining, 1),
                        "invalid_timer": "N/A",
                        "hold_down_timer": "N/A",
                        "flush_timer": "N/A",
                    }

                    continue

                # ==========================
                # RIP ROUTE
                # ==========================

                time_elapsed = current_time - info["timestamp"]

                invalid_remaining = max(
                    0,
                    INVALID_TIMER - time_elapsed
                )

                flush_remaining = max(
                    0,
                    FLUSH_TIMER - time_elapsed
                )

                hold_down_remaining = max(
                    0,
                    info.get("hold_down_until", 0) - current_time
                )

                # --------------------------
                # VALID
                # --------------------------

                status = "VALID"

                # --------------------------
                # INVALID
                # --------------------------

                if (
                    info["metric"] < INFINITY
                    and time_elapsed >= INVALID_TIMER
                ):

                    info["metric"] = INFINITY
                    info["hold_down_until"] = (
                        current_time + HOLD_DOWN_TIMER
                    )

                    status = "INVALID"
                    route_changed = True

                    logging.warning(
                        f"[{self.router_id}] "
                        f"Route {dest} became INVALID."
                    )

                # --------------------------
                # HOLD DOWN
                # --------------------------

                elif (
                    info["metric"] >= INFINITY
                    and hold_down_remaining > 0
                ):

                    status = "HOLD_DOWN"

                # --------------------------
                # FLUSH
                # --------------------------

                if time_elapsed >= FLUSH_TIMER:

                    status = "FLUSH"
                    routes_to_delete.append(dest)

                timers_info[dest] = {
                    "metric": info["metric"],
                    "status": status,
                    "update_timer": round(update_remaining, 1),
                    "invalid_timer": round(invalid_remaining, 1),
                    "hold_down_timer": round(hold_down_remaining, 1),
                    "flush_timer": round(flush_remaining, 1),
                }

            # ==========================
            # DELETE FLUSHED ROUTES
            # ==========================

            for dest in routes_to_delete:

                if dest in self.routing_table:

                    del self.routing_table[dest]
                    # Emit số lượng route bị flush
                    # self.signals.route_flushed.emit(1)

                    logging.warning(
                        f"[{self.router_id}] "
                        f"Route {dest} flushed."
                    )

                    route_changed = True

            # ==========================
            # TRIGGERED UPDATE
            # ==========================

            if route_changed:
                self.send_triggered_update()

                self.signals.router_updated.emit(
                    self.router_id,
                    self.routing_table
                )

            # ==========================
            # UPDATE TIMER GUI
            # ==========================

            self.signals.timer_updated.emit(
                self.router_id,
                timers_info
            )

            time.sleep(1)

    def receive_bytes_from_module1(self, raw_bytes, incoming_interface, neighbor_ip):
        """
        Hàm cầu nối: Module 1 sẽ gọi hàm này khi có gói tin truyền tới cổng
        """
        self.processor.process_incoming_update(
            raw_bytes, neighbor_ip, incoming_interface)

        # Phát tín hiệu cập nhật lên GUI
        self.signals.router_updated.emit(self.router_id, self.routing_table)
