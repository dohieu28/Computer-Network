from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import json


@dataclass
class TopologyNode:
    node_id: str
    node_type: str = "router"
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "data": dict(self.data),
        }


@dataclass
class TopologyLink:
    source: str
    target: str
    source_interface: Optional[str] = None
    target_interface: Optional[str] = None
    cost: int = 1
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "source_interface": self.source_interface,
            "target_interface": self.target_interface,
            "cost": self.cost,
            "data": dict(self.data),
        }


class TopologyManager:
    """Maintains topology state and handles JSON import/export."""

    def __init__(self):
        self.nodes: Dict[str, TopologyNode] = {}
        self.links: List[TopologyLink] = []

    def add_node(self, node_id: str, node_type: str = "router", **data: Any) -> TopologyNode:
        node = TopologyNode(
            node_id=node_id, node_type=node_type, data=dict(data))
        self.nodes[node_id] = node
        return node

    def add_link(
        self,
        source: str,
        target: str,
        source_interface: Optional[str] = None,
        target_interface: Optional[str] = None,
        cost: int = 1,
        **data: Any,
    ) -> TopologyLink:
        if source not in self.nodes:
            self.add_node(source)
        if target not in self.nodes:
            self.add_node(target)

        link = TopologyLink(
            source=source,
            target=target,
            source_interface=source_interface,
            target_interface=target_interface,
            cost=cost,
            data=dict(data),
        )
        self.links.append(link)
        return link

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.links = [link for link in self.links if link.source !=
                      node_id and link.target != node_id]

    def remove_link(self, source: str, target: str) -> None:
        self.links = [link for link in self.links if not (
            link.source == source and link.target == target)]

    def export_topology(self, json_file: str | Path) -> Path:
        path = Path(json_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "links": [link.to_dict() for link in self.links],
        }
        path.write_text(json.dumps(payload, indent=2,
                        ensure_ascii=False), encoding="utf-8")
        return path

    def load_topology(self, json_file: str | Path) -> None:
        path = Path(json_file)
        payload = json.loads(path.read_text(encoding="utf-8"))

        self.nodes.clear()
        self.links.clear()

        for node_data in payload.get("nodes", []):
            self.nodes[node_data["node_id"]] = TopologyNode(
                node_id=node_data["node_id"],
                node_type=node_data.get("node_type", "router"),
                data=dict(node_data.get("data", {})),
            )

        for link_data in payload.get("links", []):
            self.links.append(
                TopologyLink(
                    source=link_data["source"],
                    target=link_data["target"],
                    source_interface=link_data.get("source_interface"),
                    target_interface=link_data.get("target_interface"),
                    cost=link_data.get("cost", 1),
                    data=dict(link_data.get("data", {})),
                )
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "links": [link.to_dict() for link in self.links],
        }
