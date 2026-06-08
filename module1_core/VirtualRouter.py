from module1_core.Interface import Interface
from typing import Any, Dict, Callable, List, Optional

PacketHandler = Callable[["VirtualRouter", Any, bytes], Any]


class VirtualRouter:
    """Core virtual router abstraction.

    Parameters
    ----------
    router_id:
        Unique router identifier.
    protocol_handler:
        Optional callback invoked by `receive_packet` with signature
        `(router, incoming_interface, raw_bytes)`.
    """

    def __init__(self, router_id: str, protocol_handler: Optional[PacketHandler] = None):
        self.router_id = router_id
        self.interfaces: Dict[str, Interface] = {}
        self._routing_table: Dict[str, Dict[str, Any]] = {}
        self.protocol_handler = protocol_handler
        self.received_packets: List[Dict[str, Any]] = []
        self._seen_packet_signatures: set[tuple[Any, bytes]] = set()

    def add_interface(self, interface_obj: Interface) -> None:
        if not isinstance(interface_obj, Interface):
            raise TypeError("interface_obj must be an Interface instance")
        self.interfaces[interface_obj.interface_id] = interface_obj

    def set_route(
        self,
        destination: str,
        next_hop: Optional[str],
        outgoing_interface: Optional[str],
        metric: int,
        protocol: str = "static",
    ) -> None:
        self._routing_table[destination] = {
            "destination": destination,
            "next_hop": next_hop,
            "outgoing_interface": outgoing_interface,
            "metric": metric,
            "protocol": protocol,
        }

    def get_routing_table(self) -> Dict[str, Dict[str, Any]]:
        return {destination: dict(entry) for destination, entry in self._routing_table.items()}

    def receive_packet(self, incoming_interface: Any, raw_bytes: bytes) -> Any:
        if not isinstance(raw_bytes, (bytes, bytearray)):
            raise TypeError("raw_bytes must be bytes or bytearray")

        packet_bytes = bytes(raw_bytes)
        interface_id = getattr(
            incoming_interface, "interface_id", incoming_interface)
        packet_signature = (interface_id, packet_bytes)

        if packet_signature in self._seen_packet_signatures:
            return None
        self._seen_packet_signatures.add(packet_signature)

        packet_record = {
            "incoming_interface": interface_id,
            "raw_bytes": packet_bytes,
            "size": len(packet_bytes),
        }
        self.received_packets.append(packet_record)

        if self.protocol_handler is not None:
            return self.protocol_handler(self, incoming_interface, packet_bytes)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "router_id": self.router_id,
            "interfaces": [interface.to_dict() for interface in self.interfaces.values()],
            "routing_table": self.get_routing_table(),
        }
