from datetime import datetime


# class PacketSniffer:

#     def __init__(self, signal_hub):
#         self.captured_packets = []
#         self.signal_hub = signal_hub

#     def analyze_packet(self, raw_data, source, destination):
#         if isinstance(raw_data, str):
#             raw_data = raw_data.encode()

#         text = raw_data.decode(errors="ignore")

#         if "RIP" in text:
#             protocol = "RIP"
#         elif "OSPF" in text:
#             protocol = "OSPF"
#         elif "ARP" in text:
#             protocol = "ARP"
#         else:
#             protocol = "UNKNOWN"

#         packet_info = {
#             "time": datetime.now().strftime("%H:%M:%S"),
#             "source": source,
#             "destination": destination,
#             "protocol": protocol,
#             "length": len(raw_data)
#         }

#         self.captured_packets.append(packet_info)

#         return packet_info


class PacketSniffer:
    def __init__(self, signal_hub):
        self.signal_hub = signal_hub
        self.packet_count = 0

    def start_capture(self, target_link):
        """Hook (móc) vào dây cáp từ xa"""
        # Bơm hàm analyze_bytes của sniffer vào dây cáp
        target_link.sniffer_callback = self.analyze_bytes

    def analyze_bytes(self, raw_bytes):
        """Dây cáp sẽ tự động gọi hàm này mỗi khi có gói tin đi qua"""
        self.packet_count += 1

        # Dùng Scapy để dịch nhanh (Tầng UI chỉ cần biết loại gói, không cần tính toán logic)
        from scapy.all import Ether, IP, UDP
        packet = Ether(raw_bytes)

        protocol = "UNKNOWN"
        if packet.haslayer(UDP) and packet[UDP].dport == 520:
            protocol = "RIPv2"
        elif packet.haslayer(IP) and packet[IP].proto == 89:
            protocol = "OSPF"

        packet_info = {
            "no": self.packet_count,
            "protocol": protocol,
            "info": packet.summary()
        }

        # Hiển thị lên UI (Lưu ý: Thực tế cũng nên dùng pyqtSignal ở đây để đẩy lên UI)
        print(f"Bắt được gói {self.packet_count}: Giao thức {protocol}")

        self.signal_hub.packet_captured.emit(packet_info)
