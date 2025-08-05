from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Admin(TimestampMixin, Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, default="admin")
    is_super = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="admin")

    __table_args__ = (Index("ix_admin_user_id", "user_id"),)
