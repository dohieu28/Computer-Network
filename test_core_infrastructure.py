# test.py

import time

from module1_core.Interface import Interface
from module1_core.Link import Link


class DummyRouter:

    def __init__(self, router_id):
        self.router_id = router_id

    def receive_packet(
        self,
        incoming_interface,
        raw_bytes
    ):
        print(
            f"[{self.router_id}] "
            f"Receive: {raw_bytes}"
        )


def packet_sniffer(
    raw_bytes,
    src_interface,
    dst_interface,
    link
):
    print(
        f"[SNIFFER] "
        f"{src_interface.ip_address}"
        f" -> "
        f"{dst_interface.ip_address}"
        f" | {raw_bytes}"
    )


if __name__ == "__main__":

    r1_if = Interface(
        "192.168.1.1",
        "AA:AA:AA:AA:AA:01"
    )

    r2_if = Interface(
        "192.168.1.2",
        "AA:AA:AA:AA:AA:02"
    )

    r1 = DummyRouter("R1")
    r2 = DummyRouter("R2")

    r1_if.owner_router = r1
    r2_if.owner_router = r2

    link = Link(
        r1_if,
        r2_if,
        cost=1,
        delay=1
    )

    link.register_sniffer(packet_sniffer)

    r1_if.send(b"HELLO RIP")

    time.sleep(2)
