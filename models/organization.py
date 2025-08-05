from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(String(255))
    parent_id = Column(Integer, ForeignKey("organizations.id"))

    parent = relationship("Organization", remote_side=[id], backref="children")
    departments = relationship("Department", back_populates="organization")
    users = relationship("User", back_populates="organization")

    __table_args__ = (Index("ix_org_parent", "parent_id"),)
