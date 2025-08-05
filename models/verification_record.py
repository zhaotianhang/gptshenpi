from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, String, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class VerificationStatus(PyEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class VerificationRecord(TimestampMixin, Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("approval_forms.id"), nullable=False)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING, nullable=False)
    verified_at = Column(DateTime)
    comments = Column(String(255))

    form = relationship("ApprovalForm", back_populates="verification_records")
    verifier = relationship("User", back_populates="verification_records")

    __table_args__ = (
        Index("ix_verify_form", "form_id"),
        Index("ix_verify_verifier", "verifier_id"),
    )
