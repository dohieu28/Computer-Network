import time
import threading
import logging
from scapy.all import Ether, IP, UDP, RIP, RIPEntry
from module2_rip.RIPPacketProcessor import RIPPacketProcessor
from module4_ui.RouterSignal import RouterSignal

# Cấu hình logging để debug dễ dàng trên Terminal
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

# Constants cho Timers của RIP (Có thể thu nhỏ lại để test cho nhanh, vd: 3, 18, 24)
UPDATE_TIMER = 30
INVALID_TIMER = 180
FLUSH_TIMER = 240
INFINITY = 16


# class RIPPacketProcessor:
#     """
#     Class phụ trách bóc tách mảng Byte và chạy thuật toán Bellman-Ford
#     """

#     def __init__(self, router):
#         self.router = router  # Nhận tham chiếu đến Router đang chứa nó

#     def parse_rip_packet(self, raw_bytes):
#         """Dịch ngược mảng byte thô thành Object của Scapy"""
#         try:
#             packet = Ether(raw_bytes)
#             if packet.haslayer(RIP):
#                 return packet
#             return None
#         except Exception as e:
#             logging.error(f"Lỗi khi parse gói tin: {e}")
#             return None

#     def process_incoming_update(self, raw_bytes, neighbor_ip, incoming_interface):
#         """
#         Bóc tách gói tin và chạy thuật toán Bellman-Ford để cập nhật Routing Table
#         """
#         packet = self.parse_rip_packet(raw_bytes)
#         if not packet or not packet.haslayer(RIP):
#             return

#         rip_layer = packet[RIP]

#         # Chỉ xử lý các gói Response (Routing Update)
#         if rip_layer.cmd != 2:
#             return

#         route_changed = False

#         # Lặp qua từng mạng được quảng bá trong gói RIP
#         # scapy lưu các entry thành 1 mảng trong rip_layer
#         for i in range(1, 26):  # Một gói RIP tối đa chứa 25 routes
#             try:
#                 entry = packet.getlayer(RIPEntry, i)
#                 if entry is None:
#                     break
#             except:
#                 break

#             dest_network = entry.addr
#             metric_in = entry.metric

#             # Thuật toán Bellman-Ford: metric mới = metric hàng xóm gửi + 1
#             new_metric = min(metric_in + 1, INFINITY)

#             current_route = self.router.routing_table.get(dest_network)

#             # Trường hợp 1: Mạng mới hoàn toàn -> Thêm vào bảng
#             if current_route is None and new_metric < INFINITY:
#                 self.router.routing_table[dest_network] = {
#                     'metric': new_metric,
#                     'next_hop': neighbor_ip,
#                     'interface': incoming_interface,
#                     'timestamp': time.time()
#                 }
#                 route_changed = True
#                 logging.info(
#                     f"[{self.router.router_id}] Đã thêm mạng mới: {dest_network} qua {neighbor_ip} (Metric: {new_metric})")

#             # Trường hợp 2: Đã có mạng này trong bảng
#             elif current_route is not None:
#                 # Nếu thông tin đến từ chính Next Hop hiện tại -> Bắt buộc cập nhật (dù metric tăng hay giảm)
#                 if current_route['next_hop'] == neighbor_ip:
#                     current_route['timestamp'] = time.time()  # Reset timer
#                     if current_route['metric'] != new_metric:
#                         current_route['metric'] = new_metric
#                         route_changed = True
#                         logging.info(
#                             f"[{self.router.router_id}] Cập nhật metric mạng {dest_network} thành {new_metric} từ {neighbor_ip}")

#                 # Nếu thông tin đến từ Next Hop khác, nhưng có metric nhỏ hơn (đường đi tốt hơn) -> Cập nhật
#                 elif new_metric < current_route['metric']:
#                     self.router.routing_table[dest_network] = {
#                         'metric': new_metric,
#                         'next_hop': neighbor_ip,
#                         'interface': incoming_interface,
#                         'timestamp': time.time()
#                     }
#                     route_changed = True
#                     logging.info(
#                         f"[{self.router.router_id}] Tìm thấy đường đi tốt hơn tới {dest_network} qua {neighbor_ip} (Metric: {new_metric})")

#         # Kích hoạt Gửi Update khẩn cấp (Triggered Update) nếu có sự thay đổi
#         if route_changed:
#             self.router.send_triggered_update()


class RIPRouter:
    """
    Lớp định tuyến RIP, kế thừa (hoặc hoạt động cùng) VirtualRouter ở Module 1
    """

    def __init__(self, router_id, ip):
        self.router_id = router_id
        self.ip = ip
        self.signals = RouterSignal()
        # Danh sách các cổng mạng (Sẽ do Module 1 cung cấp)
        self.interfaces = []

        # Cấu trúc bảng định tuyến:
        # { '10.0.0.0': {'metric': 1, 'next_hop': '192.168.1.2', 'interface': 'eth0', 'timestamp': 1600000.0} }
        self.routing_table = {}

        self.processor = RIPPacketProcessor(self)
        self.running = False

    def add_direct_route(self, network_ip, interface_name):
        """Thêm mạng kết nối trực tiếp (Metric = 0)"""
        self.routing_table[network_ip] = {
            'metric': 0,
            'next_hop': '0.0.0.0',  # Kết nối trực tiếp
            'interface': interface_name,
            # Routes trực tiếp thường không bao giờ hết hạn, cần xử lý logic riêng
            'timestamp': time.time()
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
        routes_to_send = self.apply_split_horizon(
            self.routing_table, target_interface, poison_reverse=True)

        if not routes_to_send:
            return None

        # Khởi tạo gói tin Multicast chuẩn RIPv2
        eth_layer = Ether(dst="01:00:5E:00:00:09")  # Multicast MAC
        # Multicast IP RIPv2
        ip_layer = IP(src=self.ip, dst="224.0.0.9")
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
                logging.debug(
                    f"[{self.router_id}] Đã gửi RIP Update ra cổng {interface.name}")

    def send_triggered_update(self):
        """Gửi ngay lập tức khi mạng có biến (Không đợi 30s)"""
        logging.info(f"[{self.router_id}] Kích hoạt Triggered Update!")
        self.send_update_out_all_interfaces()

        # Bắn tín hiệu lên GUI (Module 4) ở đây
        # Example: signal_ui_update(self.router_id, self.routing_table)

    def _periodic_update_loop(self):
        """Luồng đếm ngược 30s"""
        while self.running:
            self.send_update_out_all_interfaces()
            time.sleep(UPDATE_TIMER)

    def _timer_check_loop(self):
        """Luồng quét và đánh dấu mạng chết (Invalid) hoặc xóa (Flush)"""
        while self.running:
            current_time = time.time()
            routes_to_delete = []
            route_changed = False

            for dest, info in self.routing_table.items():
                if info['metric'] == 0:
                    continue  # Không áp dụng timer cho mạng kết nối trực tiếp

                time_elapsed = current_time - info['timestamp']

                if time_elapsed > FLUSH_TIMER:
                    routes_to_delete.append(dest)
                elif time_elapsed > INVALID_TIMER and info['metric'] != INFINITY:
                    info['metric'] = INFINITY
                    route_changed = True
                    logging.warning(
                        f"[{self.router_id}] Mạng {dest} đã Unreachable (Vượt {INVALID_TIMER}s)")

            for dest in routes_to_delete:
                del self.routing_table[dest]
                route_changed = True
                logging.warning(
                    f"[{self.router_id}] Đã xóa mạng {dest} khỏi bảng (Vượt {FLUSH_TIMER}s)")

            if route_changed:
                self.send_triggered_update()

            time.sleep(2)  # Quét mỗi 2s

    def receive_bytes_from_module1(self, raw_bytes, incoming_interface, neighbor_ip):
        """
        Hàm cầu nối: Module 1 sẽ gọi hàm này khi có gói tin truyền tới cổng
        """
        self.processor.process_incoming_update(
            raw_bytes, neighbor_ip, incoming_interface)

        # Phát tín hiệu cập nhật lên GUI
        self.signals.router_updated.emit(self.router_id, self.routing_table)
