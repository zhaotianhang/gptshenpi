from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class SubmissionRecord(TimestampMixin, Base):
    __tablename__ = "submission_records"

    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey("approval_forms.id"), nullable=False)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime)

    form = relationship("ApprovalForm", back_populates="submission_records")
    submitter = relationship("User", back_populates="submission_records")

    __table_args__ = (
        Index("ix_submission_form", "form_id"),
        Index("ix_submission_submitter", "submitter_id"),
    )
