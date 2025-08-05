from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, unique=True)
    email = Column(String(128), unique=True)
    password_hash = Column(String(128), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    is_active = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users")
    admin = relationship("Admin", uselist=False, back_populates="user")
    approval_forms = relationship("ApprovalForm", back_populates="applicant")
    approval_records = relationship(
        "ApprovalRecord", back_populates="approver", foreign_keys="ApprovalRecord.approver_id"
    )
    delegated_records = relationship(
        "ApprovalRecord",
        back_populates="delegated_to",
        foreign_keys="ApprovalRecord.delegated_to_id",
    )
    submission_records = relationship("SubmissionRecord", back_populates="submitter")
    verification_records = relationship("VerificationRecord", back_populates="verifier")
    notifications = relationship("Notification", back_populates="recipient")

    __table_args__ = (
        Index("ix_user_org", "organization_id"),
        Index("ix_user_dept", "department_id"),
    )
