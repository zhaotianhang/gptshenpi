from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ApprovalTemplate(TimestampMixin, Base):
    __tablename__ = "approval_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(String(255))
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    steps = Column(JSON, nullable=False)

    creator = relationship("User")
    forms = relationship("ApprovalForm", back_populates="template")

    __table_args__ = (Index("ix_template_creator", "creator_id"),)
