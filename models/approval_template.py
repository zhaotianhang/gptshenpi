from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class NodeType(PyEnum):
    START = "start"
    APPROVAL = "approval"
    PUSH = "push"
    CONDITION = "condition"
    END = "end"


class ApprovalTemplate(TimestampMixin, Base):
    __tablename__ = "approval_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    version = Column(String(50), default="1.0")
    is_active = Column(Integer, default=1)  # 1: active, 0: inactive
    
    # 流程配置
    workflow_config = Column(JSON, nullable=False, default=dict)
    
    # 关联关系
    forms = relationship("ApprovalForm", back_populates="template")

    __table_args__ = (
        Index("ix_template_name", "name"),
        Index("ix_template_active", "is_active"),
    )

    def get_workflow_nodes(self):
        """获取流程节点"""
        return self.workflow_config.get('nodes', [])
    
    def get_start_node(self):
        """获取开始节点"""
        nodes = self.get_workflow_nodes()
        return next((node for node in nodes if node.get('type') == NodeType.START.value), None)
    
    def get_approval_nodes(self):
        """获取审批节点"""
        nodes = self.get_workflow_nodes()
        return [node for node in nodes if node.get('type') == NodeType.APPROVAL.value]
    
    def get_node_by_id(self, node_id):
        """根据ID获取节点"""
        nodes = self.get_workflow_nodes()
        return next((node for node in nodes if node.get('id') == node_id), None)
    
    def get_next_nodes(self, current_node_id):
        """获取当前节点的下一个节点"""
        current_node = self.get_node_by_id(current_node_id)
        if not current_node:
            return []
        
        next_node_ids = current_node.get('next', [])
        return [self.get_node_by_id(node_id) for node_id in next_node_ids if self.get_node_by_id(node_id)]
    
    def validate_workflow(self):
        """验证流程配置"""
        nodes = self.get_workflow_nodes()
        if not nodes:
            return False, "流程节点不能为空"
        
        # 检查是否有开始节点
        start_nodes = [node for node in nodes if node.get('type') == NodeType.START.value]
        if len(start_nodes) != 1:
            return False, "必须有且仅有一个开始节点"
        
        # 检查是否有结束节点
        end_nodes = [node for node in nodes if node.get('type') == NodeType.END.value]
        if len(end_nodes) == 0:
            return False, "必须有至少一个结束节点"
        
        # 检查节点连接
        node_ids = {node.get('id') for node in nodes}
        for node in nodes:
            next_ids = node.get('next', [])
            for next_id in next_ids:
                if next_id not in node_ids:
                    return False, f"节点 {node.get('id')} 连接到不存在的节点 {next_id}"
        
        return True, "流程配置有效"
