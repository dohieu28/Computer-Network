=== VirtualRouter demo ===
[PROTOCOL] Packet received
  Router: R1
  Incoming interface: eth0
  Raw bytes: b'E\x00\x00Tdemo-packet'
  Size: 15 bytes
Protocol handler response: {'status': 'ok', 'size': 15}
Duplicate packet response: None
Routing table:
  0.0.0.0/0: {'destination': '0.0.0.0/0', 'next_hop': '10.0.0.2', 'outgoing_interface': 'eth0', 'metric': 1, 'protocol': 'static'}
  192.168.1.0/24: {'destination': '192.168.1.0/24', 'next_hop': None, 'outgoing_interface': 'eth1', 'metric': 0, 'protocol': 'connected'}

=== TopologyManager demo ===
Exported topology to: D:\TUAN TU\Bài tập lớn Mạng máy tính\demo_topology.json
Loaded topology:
{'nodes': [{'node_id': 'R1', 'node_type': 'router', 'data': {'label': 'Router 1'}}, {'node_id': 'R2', 'node_type': 'router', 'data': {'label': 'Router 2'}}], 'links': [{'source': 'R1', 'target': 'R2', 'source_interface': 'eth0', 'target_interface': 'eth0', 'cost': 1, 'data': {'bandwidth': '1Gbps'}}]}
