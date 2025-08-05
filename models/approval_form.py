from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    JSON,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class FormStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalForm(TimestampMixin, Base):
    __tablename__ = "approval_forms"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("approval_templates.id"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    status = Column(Enum(FormStatus), default=FormStatus.PENDING, nullable=False)
    data = Column(JSON, nullable=False)

    template = relationship("ApprovalTemplate", back_populates="forms")
    applicant = relationship("User", back_populates="approval_forms")
    department = relationship("Department", back_populates="approval_forms")
    approval_records = relationship(
        "ApprovalRecord", back_populates="form", cascade="all, delete-orphan"
    )
    submission_records = relationship(
        "SubmissionRecord", back_populates="form", cascade="all, delete-orphan"
    )
    verification_records = relationship(
        "VerificationRecord", back_populates="form", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_form_template", "template_id"),
        Index("ix_form_applicant", "applicant_id"),
        Index("ix_form_status", "status"),
    )
