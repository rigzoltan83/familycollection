"""
Household SQLAlchemy modell.

Egy Household egy családot, háztartást vagy közösen kezelt
gyűjteményt jelöl.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    members: Mapped[list["HouseholdMember"]] = relationship(
        back_populates="household",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"Household(id={self.id!r}, "
            f"name={self.name!r}, "
            f"slug={self.slug!r})"
        )
