from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))

    organization = relationship("Organization", back_populates="departments")
    parent = relationship("Department", remote_side=[id], backref="children")
    manager = relationship("User")
    users = relationship("User", back_populates="department")
    approval_forms = relationship("ApprovalForm", back_populates="department")

    __table_args__ = (
        Index("ix_dept_org", "organization_id"),
        Index("ix_dept_parent", "parent_id"),
    )
