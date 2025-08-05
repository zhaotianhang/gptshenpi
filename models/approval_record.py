from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Enum,
    String,
    DateTime,
    Index,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ActionType(PyEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    SUBMITTED = "submitted"


class ApprovalRecord(TimestampMixin, Base):
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("approval_forms.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submission_record_id = Column(
        Integer, ForeignKey("submission_records.id"), nullable=True
    )
    result = Column(Enum(ActionType), nullable=False)
    comments = Column(String(255))
    acted_at = Column(DateTime)
    delegated_to_id = Column(Integer, ForeignKey("users.id"))
    step = Column(Integer)

    form = relationship("ApprovalForm", back_populates="approval_records")
    approver = relationship(
        "User", back_populates="approval_records", foreign_keys=[approver_id]
    )
    submission_record = relationship(
        "SubmissionRecord", back_populates="approval_records"
    )
    delegated_to = relationship(
        "User", back_populates="delegated_records", foreign_keys=[delegated_to_id]
    )

    __table_args__ = (
        Index("ix_record_form", "form_id"),
        Index("ix_record_approver", "approver_id"),
    )
