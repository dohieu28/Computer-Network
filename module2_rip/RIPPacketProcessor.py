import time
import logging
from scapy.all import Ether, RIP, RIPEntry

# Constants cho Timers của RIP (Có thể thu nhỏ lại để test cho nhanh, vd: 3, 18, 24)
UPDATE_TIMER = 30
INVALID_TIMER = 180
FLUSH_TIMER = 240
INFINITY = 16


class RIPPacketProcessor:
    """
    Class phụ trách bóc tách mảng Byte và chạy thuật toán Bellman-Ford
    """

    def __init__(self, router):
        self.router = router  # Nhận tham chiếu đến Router đang chứa nó

    def parse_rip_packet(self, raw_bytes):
        """Dịch ngược mảng byte thô thành Object của Scapy"""
        try:
            packet = Ether(raw_bytes)
            if packet.haslayer(RIP):
                return packet
            return None
        except Exception as e:
            logging.error(f"Lỗi khi parse gói tin: {e}")
            return None

    def process_incoming_update(self, raw_bytes, neighbor_ip, incoming_interface):
        """
        Bóc tách gói tin và chạy thuật toán Bellman-Ford để cập nhật Routing Table
        """
        packet = self.parse_rip_packet(raw_bytes)
        if not packet or not packet.haslayer(RIP):
            return

        rip_layer = packet[RIP]

        # Chỉ xử lý các gói Response (Routing Update)
        if rip_layer.cmd != 2:
            return

        route_changed = False

        # Lặp qua từng mạng được quảng bá trong gói RIP
        # scapy lưu các entry thành 1 mảng trong rip_layer
        for i in range(1, 26):  # Một gói RIP tối đa chứa 25 routes
            try:
                entry = packet.getlayer(RIPEntry, i)
                if entry is None:
                    break
            except:
                break

            dest_network = entry.addr
            metric_in = entry.metric

            # Thuật toán Bellman-Ford: metric mới = metric hàng xóm gửi + 1
            new_metric = min(metric_in + 1, INFINITY)

            current_route = self.router.routing_table.get(dest_network)

            # Trường hợp 1: Mạng mới hoàn toàn -> Thêm vào bảng
            if current_route is None and new_metric < INFINITY:
                self.router.routing_table[dest_network] = {
                    'metric': new_metric,
                    'next_hop': neighbor_ip,
                    'interface': incoming_interface,
                    'timestamp': time.time()
                }
                route_changed = True
                logging.info(
                    f"[{self.router.router_id}] Đã thêm mạng mới: {dest_network} qua {neighbor_ip} (Metric: {new_metric})")

            # Trường hợp 2: Đã có mạng này trong bảng
            elif current_route is not None:
                # Nếu thông tin đến từ chính Next Hop hiện tại -> Bắt buộc cập nhật (dù metric tăng hay giảm)
                if current_route['next_hop'] == neighbor_ip:
                    current_route['timestamp'] = time.time()  # Reset timer
                    if current_route['metric'] != new_metric:
                        current_route['metric'] = new_metric
                        route_changed = True
                        logging.info(
                            f"[{self.router.router_id}] Cập nhật metric mạng {dest_network} thành {new_metric} từ {neighbor_ip}")

                # Nếu thông tin đến từ Next Hop khác, nhưng có metric nhỏ hơn (đường đi tốt hơn) -> Cập nhật
                elif new_metric < current_route['metric']:
                    self.router.routing_table[dest_network] = {
                        'metric': new_metric,
                        'next_hop': neighbor_ip,
                        'interface': incoming_interface,
                        'timestamp': time.time()
                    }
                    route_changed = True
                    logging.info(
                        f"[{self.router.router_id}] Tìm thấy đường đi tốt hơn tới {dest_network} qua {neighbor_ip} (Metric: {new_metric})")

        # Kích hoạt Gửi Update khẩn cấp (Triggered Update) nếu có sự thay đổi
        if route_changed:
            self.router.send_triggered_update()
