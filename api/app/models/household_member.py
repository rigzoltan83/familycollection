"""
HouseholdMember SQLAlchemy modell.

A felhasználók és a háztartások közötti tagságot tárolja,
a háztartáson belüli szerepkörrel együtt.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class HouseholdMember(Base):
    __tablename__ = "household_members"

    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "user_id",
            name="uq_household_members_household_user",
        ),
        CheckConstraint(
            "role IN ('owner', 'admin', 'editor', 'viewer')",
            name="ck_household_members_role",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    household_id: Mapped[int] = mapped_column(
        ForeignKey(
            "households.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="viewer",
        server_default="viewer",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    household: Mapped["Household"] = relationship(
        back_populates="members",
    )

    user: Mapped["User"] = relationship(
        back_populates="household_memberships",
    )

    def __repr__(self) -> str:
        return (
            f"HouseholdMember(id={self.id!r}, "
            f"household_id={self.household_id!r}, "
            f"user_id={self.user_id!r}, "
            f"role={self.role!r})"
        )
