# interface.py

from typing import Optional


class Interface:
    """
    Đại diện cho một cổng mạng (Network Interface Card - NIC).

    Mỗi Router có thể có nhiều Interface.
    Interface chịu trách nhiệm:
        - Lưu địa chỉ IP và MAC
        - Kết nối với một Link
        - Gửi dữ liệu xuống Link

    Ví dụ:

        Router R1
           |
        Interface
           |
          Link

    Interface KHÔNG xử lý RIP/OSPF.
    Interface chỉ truyền raw bytes.
    """

    def __init__(self, ip_address: str, mac_address: str):
        self.ip_address = ip_address
        self.mac_address = mac_address

        self.link_obj: Optional["Link"] = None
        self.owner_router = None

    def connect_link(self, link_obj):
        """
        Gắn Interface vào một Link.
        """
        self.link_obj = link_obj

    def send(self, raw_bytes: bytes):
        """
        Gửi dữ liệu xuống Link.
        """
        if self.link_obj is None:
            raise RuntimeError(
                f"Interface {self.ip_address} chưa kết nối Link."
            )

        self.link_obj.transmit(self, raw_bytes)

    def __str__(self):
        return f"Interface(IP={self.ip_address}, MAC={self.mac_address})"