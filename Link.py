# link.py

import time
import threading


class Link:
    """
    Mô phỏng một đường truyền vật lý giữa hai Interface.

    Chức năng:
        - Kết nối hai Interface
        - Truyền raw bytes
        - Mô phỏng delay mạng
        - Mô phỏng đứt cáp (UP/DOWN)
        - Cho PacketSniffer nghe lén packet

    Ví dụ:

        Interface A
              |
            Link
              |
        Interface B
    """
    def __init__(
        self,
        interface_a,
        interface_b,
        cost=1,
        delay=0.1
    ):
        self.interface_a = interface_a
        self.interface_b = interface_b

        self.cost = cost
        self.delay = delay

        self.status = "UP"

        self.sniffers = []

        interface_a.connect_link(self)
        interface_b.connect_link(self)

    def set_status(self, status):
        """
    Thay đổi trạng thái Link.

    UP:
        Packet được truyền bình thường.

    DOWN:
        Packet bị loại bỏ (drop).

    Dùng để mô phỏng:
        - Đứt cáp
        - Mất kết nối
        - Sự cố mạng
     """
        status = status.upper()

        if status not in ["UP", "DOWN"]:
            raise ValueError("Status phải là UP hoặc DOWN")

        self.status = status

    def register_sniffer(self, callback):
        """
    Đăng ký Packet Sniffer.

    Mỗi khi packet đi qua Link,
    callback sẽ nhận được một bản sao packet.

    Parameters
    ----------
    callback :
        Hàm có dạng:

        callback(
            raw_bytes,
            src_interface,
            dst_interface,
            link
        )
    """
        self.sniffers.append(callback)

    def _get_destination(self, src_interface):
        if src_interface == self.interface_a:
            return self.interface_b

        if src_interface == self.interface_b:
            return self.interface_a

        raise ValueError(
            "Interface gửi không thuộc Link này"
        )

    def transmit(self, src_interface, raw_bytes):
        """
    Truyền dữ liệu từ Interface nguồn
    sang Interface đích.

    Flow:

        Router
          ↓
      Interface.send()
          ↓
      Link.transmit()
          ↓
      Delay Simulation
          ↓
      Destination Interface
          ↓
      Destination Router
    """

        if self.status == "DOWN":
            print(
                f"[LINK DOWN] Drop packet from "
                f"{src_interface.ip_address}"
            )
            return

        dst_interface = self._get_destination(src_interface)

        # Copy packet cho sniffer
        for callback in self.sniffers:
            try:
                callback(
                    raw_bytes,
                    src_interface,
                    dst_interface,
                    self
                )
            except Exception as ex:
                print(f"[SNIFFER ERROR] {ex}")

        def deliver():
            time.sleep(self.delay)

            if dst_interface.owner_router:
                dst_interface.owner_router.receive_packet(
                    dst_interface,
                    raw_bytes
                )
            else:
                print(
                    f"[DELIVER] "
                    f"{src_interface.ip_address}"
                    f" -> "
                    f"{dst_interface.ip_address}"
                )

        threading.Thread(
            target=deliver,
            daemon=True
        ).start()