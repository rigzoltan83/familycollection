"""
Közös SQLAlchemy mixinek.

Az új platformmodellek egységes belső és publikus azonosítót,
valamint létrehozási és módosítási időpontot kapnak.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import generate_public_id


class PublicEntityMixin:
    """
    Közös mezők publikus platformentitásokhoz.

    A mixin nem önálló tábla, hanem más SQLAlchemy modellek
    öröklik.
    """

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    public_id: Mapped[str] = mapped_column(
        String(26),
        nullable=False,
        unique=True,
        index=True,
        default=generate_public_id,
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
