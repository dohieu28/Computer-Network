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
        else:
            protocol = "UNKNOWN"

        packet_info = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "source": source,
            "destination": destination,
            "protocol": protocol,
            "length": len(raw_data)
        }

        self.captured_packets.append(packet_info)

        return packet_info