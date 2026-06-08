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

    def __init__(self, name: str, ip: str, mac: str, owner_router):
        self.ip = ip
        self.mac = mac
        self.name = name
        self.link_obj = None
        self.owner_router = owner_router

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
                f"Interface {self.ip} chưa kết nối Link."
            )

        self.link_obj.transmit(self, raw_bytes)

    def receive_from_link(self, raw_bytes, neighbor_ip):
        """Hàm này do dây cáp (Link) gọi khi có luồng điện/byte truyền tới"""
        # Bàn giao mảng byte lên cho não bộ của Router (Module 2/3 xử lý)
        if self.owner_router:
            self.owner_router.receive_bytes_from_module1(
                raw_bytes, self.name, neighbor_ip)

    def __str__(self):
        return f"Interface(IP={self.ip}, MAC={self.mac})"
