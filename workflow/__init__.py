from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from notifications import send as send_notification


@dataclass
class Node:
    """Represents a single workflow node."""

    id: str
    type: str  # 'approval' or 'push'
    next: Optional[str] = None
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    approvers: List[int] = field(default_factory=list)
    delegates: List[int] = field(default_factory=list)
    push: List[int] = field(default_factory=list)


class Workflow:
    """Parses workflow templates and provides navigation helpers."""

    def __init__(self, nodes: Dict[str, Node], start_id: Optional[str] = None):
        self.nodes = nodes
        self.start_id = start_id

    @classmethod
    def from_template(cls, steps: List[Dict[str, Any]]):
        """Create a workflow from a template description."""
        nodes: Dict[str, Node] = {}
        start_id = steps[0]['id'] if steps else None
        for step in steps:
            node = Node(
                id=step['id'],
                type=step['type'],
                next=step.get('next'),
                conditions=step.get('conditions', []),
                approvers=step.get('approvers', []),
                delegates=step.get('delegates', []),
                push=step.get('push', []),
            )
            nodes[node.id] = node
        return cls(nodes, start_id)

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_next(self, node_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[Node]:
        """Return the next node given the current context."""
        node = self.get_node(node_id)
        if node is None:
            return None
        context = context or {}
        # Evaluate conditional jumps. Each condition is a dict with 'expr' and 'next'.
        for condition in node.conditions:
            expr = condition.get('expr')
            target = condition.get('next')
            if expr is None or target is None:
                continue
            try:
                if eval(expr, {}, context):  # nosec - expressions are controlled by templates
                    return self.get_node(target)
            except Exception:
                continue
        if node.next:
            return self.get_node(node.next)
        return None

    def next_approval(self, node_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[Node]:
        """Find the next approval node from the given node."""
        checked = set()
        nxt = self.get_next(node_id, context)
        while nxt and nxt.id not in checked:
            if nxt.type == 'approval':
                return nxt
            checked.add(nxt.id)
            nxt = self.get_next(nxt.id, context)
        return None

    def push_targets(self, node_id: str, context: Optional[Dict[str, Any]] = None) -> List[int]:
        """Return push recipients for the node.

        By default notifications are sent to the approvers of the next approval
        node. Additional recipients can be specified via the node's ``push``
        field.
        """
        node = self.get_node(node_id)
        if node is None:
            return []
        targets = list(node.push)
        nxt = self.next_approval(node_id, context)
        if nxt:
            targets.extend(nxt.approvers)
        return targets

    def notify(self, node_id: str, message: str, context: Optional[Dict[str, Any]] = None,
               channels: Optional[List[str]] = None) -> None:
        """Send a notification after the specified node is completed.

        Notifications are delivered to the next approver(s) or any additional
        push targets defined for the node.
        """
        recipients = self.push_targets(node_id, context)
        if recipients:
            send_notification(recipients, message, channels)
