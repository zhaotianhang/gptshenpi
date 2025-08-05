from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    related_form_id = Column(Integer, ForeignKey("approval_forms.id"))
    pushed_at = Column(DateTime)

    recipient = relationship("User", back_populates="notifications")
    related_form = relationship("ApprovalForm")

    __table_args__ = (
        Index("ix_notification_recipient", "recipient_id"),
        Index("ix_notification_read", "read"),
    )
