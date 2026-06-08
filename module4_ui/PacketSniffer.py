from datetime import datetime


class PacketSniffer:
    def __init__(self):
        self.captured_packets = []

    def analyze_packet(self, raw_data, source, destination):
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()

        text = raw_data.decode(errors="ignore")

        if "RIP" in text:
            protocol = "RIP"
        elif "OSPF" in text:
            protocol = "OSPF"
        elif "ARP" in text:
            protocol = "ARP"
        elif "IP" in text:
            protocol = "IP"
        else:
            protocol = "UNKNOWN"

        packet_info = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "source": source,
            "destination": destination,
            "protocol": protocol,
            "length": len(raw_data),
            "raw_bytes": raw_data
        }

        self.captured_packets.append(packet_info)
        return packet_info

    def capture_from_link(self, raw_bytes, src_interface, dst_interface, link):
        """
        Hàm này khớp với Module 1 Link.register_sniffer(callback).

        Module 1 gọi:
            callback(raw_bytes, src_interface, dst_interface, link)
        """

        source = getattr(src_interface, "ip_address", "Unknown")
        destination = getattr(dst_interface, "ip_address", "Unknown")

        return self.analyze_packet(raw_bytes, source, destination)
