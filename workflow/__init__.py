from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class ExecutionRecord:
    """Record of an executed workflow node."""

    node_id: str
    actor_id: int
    result: str  # ``approved`` or ``rejected``
    comments: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    acted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowTemplate:
    """Helper for administrators to assemble workflow templates."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    start_id: Optional[str] = None

    def add_approval(
        self,
        node_id: str,
        approvers: List[int],
        *,
        delegates: Optional[List[int]] = None,
        next: Optional[str] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
        push: Optional[List[int]] = None,
    ) -> "WorkflowTemplate":
        if not approvers:
            raise ValueError("approval node requires approvers")
        node = Node(
            id=node_id,
            type="approval",
            next=next,
            conditions=list(conditions or []),
            approvers=list(approvers),
            delegates=list(delegates or []),
            push=list(push or []),
        )
        self.nodes[node_id] = node
        if not self.start_id:
            self.start_id = node_id
        return self

    def add_push(
        self,
        node_id: str,
        *,
        push: Optional[List[int]] = None,
        next: Optional[str] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
    ) -> "WorkflowTemplate":
        node = Node(
            id=node_id,
            type="push",
            next=next,
            conditions=list(conditions or []),
            push=list(push or []),
        )
        self.nodes[node_id] = node
        if not self.start_id:
            self.start_id = node_id
        return self

    def to_workflow(self) -> "Workflow":
        return Workflow(self.nodes, self.start_id)


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
            if step.get('type') == 'approval' and not step.get('approvers'):
                raise ValueError('approval node requires approvers')
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


class WorkflowInstance:
    """Simple in-memory workflow executor."""

    def __init__(
        self,
        workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
        *,
        auto_notify_start: bool = True,
    ):
        self.workflow = workflow
        self.context = context or {}
        self.current_id = workflow.start_id
        self.records: List[ExecutionRecord] = []
        self.status = 'pending'
        if auto_notify_start and self.current_id:
            node = self.current_node()
            if node and node.type == 'approval':
                send_notification(node.approvers, f"{node.id} pending", None)

    def current_node(self) -> Optional[Node]:
        return self.workflow.get_node(self.current_id) if self.current_id else None

    def act(self, actor_id: int, result: str, comments: Optional[str] = None,
            attachments: Optional[List[str]] = None) -> None:
        """Execute the current node with the provided result."""
        node = self.current_node()
        if node is None or node.type != 'approval':
            raise ValueError('current node is not approvable')
        if actor_id not in node.approvers and actor_id not in node.delegates:
            raise ValueError('actor not permitted for this node')
        record = ExecutionRecord(
            node_id=node.id,
            actor_id=actor_id,
            result=result,
            comments=comments,
            attachments=list(attachments or []),
        )
        self.records.append(record)
        self.workflow.notify(node.id, f'{node.id} {result}', self.context)
        if result == 'approved':
            nxt = self.workflow.get_next(node.id, self.context)
            if nxt:
                self.current_id = nxt.id
            else:
                self.current_id = None
                self.status = 'approved'
        else:
            self.current_id = None
            self.status = 'rejected'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'current': self.current_id,
            'history': [r.__dict__ for r in self.records],
            'flow': self.flow_state(),
        }

    def flow_state(self) -> List[Dict[str, Any]]:
        """Return ordered node list with execution status for display."""
        order: List[Dict[str, Any]] = []
        node_id = self.workflow.start_id
        visited = set()
        while node_id and node_id not in visited:
            node = self.workflow.get_node(node_id)
            status = 'pending'
            for rec in self.records:
                if rec.node_id == node.id:
                    status = rec.result
                    break
            if node.id == self.current_id:
                status = 'in_progress'
            order.append({'id': node.id, 'type': node.type, 'status': status})
            visited.add(node_id)
            nxt = self.workflow.get_next(node_id, self.context)
            node_id = nxt.id if nxt else None
        return order
