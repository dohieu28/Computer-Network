from datetime import datetime
from scapy.all import Ether, RIP, IP, ARP, UDP
import logging

logging.basicConfig(level=logging.DEBUG)


class PacketSniffer:
    def __init__(self, signals=None):
        self.captured_packets = []
        self.signals = signals
        self.packet_no = 0

    def detect_protocol(self, raw_data):
        """Phát hiện protocol từ Scapy packet layers"""
        try:
            packet = Ether(raw_data)
            
            # Kiểm tra RIP trước (vì nó nằm sâu trong IP/UDP)
            if packet.haslayer(RIP):
                rip_layer = packet[RIP]
                return f"RIPv{rip_layer.version}"
            
            # Kiểm tra ARP
            if packet.haslayer(ARP):
                return "ARP"
            
            # Kiểm tra IP
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                
                # Kiểm tra UDP (RIP cũng dùng UDP 520)
                if packet.haslayer(UDP):
                    udp_layer = packet[UDP]
                    if udp_layer.dport == 520 or udp_layer.sport == 520:
                        return "RIP"
                    else:
                        return "UDP"
                
                return "IP"
            
            return "UNKNOWN"
        except Exception as e:
            logging.debug(f"[PacketSniffer] Protocol detection error: {e}")
            return "UNKNOWN"

    def analyze_packet(self, raw_data, source="Unknown", destination="Unknown"):
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()

        # Sử dụng Scapy để phát hiện protocol thay vì text search
        protocol = self.detect_protocol(raw_data)

        self.packet_no += 1

        packet_info = {
            "no": self.packet_no,
            "time": datetime.now().strftime("%H:%M:%S"),
            "source": source,
            "destination": destination,
            "protocol": protocol,
            "length": len(raw_data),
            "info": f"{source} -> {destination}, length={len(raw_data)}",
            "raw_bytes": raw_data,
        }

        self.captured_packets.append(packet_info)

        if self.signals is not None:
            try:
                self.signals.packet_captured.emit(packet_info)
            except Exception:
                pass

        return packet_info

    def analyze_bytes(self, raw_data, source="Unknown", destination="Unknown"):
        return self.analyze_packet(raw_data, source, destination)

    def capture_from_link(
        self,
        raw_bytes,
        src_interface=None,
        dst_interface=None,
        link=None
    ):
        """
        Dùng để đăng ký với Link.register_sniffer(callback).

        Hỗ trợ cả 2 kiểu:
        1. callback(raw_bytes)
        2. callback(raw_bytes, src_interface, dst_interface, link)
        """

        source = "Unknown"
        destination = "Unknown"

        if src_interface is not None:
            source = (
                getattr(src_interface, "ip", None)
                or getattr(src_interface, "ip_address", None)
                or getattr(src_interface, "name", None)
                or "Unknown"
            )

        if dst_interface is not None:
            destination = (
                getattr(dst_interface, "ip", None)
                or getattr(dst_interface, "ip_address", None)
                or getattr(dst_interface, "name", None)
                or "Unknown"
            )

        return self.analyze_packet(raw_bytes, source, destination)
