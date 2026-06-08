"""Quick demo script for the core infrastructure module.

Run:
    python demo_core_infrastructure.py
"""

from pathlib import Path

from core_infrastructure import Interface, TopologyManager, VirtualRouter


def protocol_handler(router: VirtualRouter, incoming_interface, raw_bytes: bytes):
    print("[PROTOCOL] Packet received")
    print(f"  Router: {router.router_id}")
    print(f"  Incoming interface: {getattr(incoming_interface, 'interface_id', incoming_interface)}")
    print(f"  Raw bytes: {raw_bytes!r}")
    print(f"  Size: {len(raw_bytes)} bytes")
    return {"status": "ok", "size": len(raw_bytes)}


def main() -> None:
    print("=== VirtualRouter demo ===")
    router = VirtualRouter("R1", protocol_handler=protocol_handler)

    iface0 = Interface(interface_id="eth0", ip_address="10.0.0.1", mac_address="00:11:22:33:44:55")
    iface1 = Interface(interface_id="eth1", ip_address="192.168.1.1", mac_address="00:11:22:33:44:66")

    router.add_interface(iface0)
    router.add_interface(iface1)
    router.set_route("0.0.0.0/0", next_hop="10.0.0.2", outgoing_interface="eth0", metric=1)
    router.set_route("192.168.1.0/24", next_hop=None, outgoing_interface="eth1", metric=0, protocol="connected")

    response = router.receive_packet(iface0, b"\x45\x00\x00\x54demo-packet")
    print("Protocol handler response:", response)
    duplicate_response = router.receive_packet(iface0, b"\x45\x00\x00\x54demo-packet")
    print("Duplicate packet response:", duplicate_response)
    print("Routing table:")
    for destination, entry in router.get_routing_table().items():
        print(f"  {destination}: {entry}")

    print("\n=== TopologyManager demo ===")
    topo = TopologyManager()
    topo.add_node("R1", node_type="router", label="Router 1")
    topo.add_node("R2", node_type="router", label="Router 2")
    topo.add_link("R1", "R2", source_interface="eth0", target_interface="eth0", cost=1, bandwidth="1Gbps")

    export_path = Path("demo_topology.json")
    topo.export_topology(export_path)
    print(f"Exported topology to: {export_path.resolve()}")

    loaded = TopologyManager()
    loaded.load_topology(export_path)
    print("Loaded topology:")
    print(loaded.to_dict())

    print("\nDemo completed successfully.")


if __name__ == "__main__":
    main()
