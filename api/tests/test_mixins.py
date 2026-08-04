from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import PublicEntityMixin


class ExamplePublicEntity(
    PublicEntityMixin,
    Base,
):
    __tablename__ = "test_public_entities"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )


def test_public_entity_mixin_adds_common_columns() -> None:
    columns = ExamplePublicEntity.__table__.columns

    assert "id" in columns
    assert "public_id" in columns
    assert "created_at" in columns
    assert "updated_at" in columns
    assert "name" in columns


def test_public_id_column_has_expected_length() -> None:
    public_id_column = ExamplePublicEntity.__table__.columns["public_id"]

    assert public_id_column.type.length == 26
    assert public_id_column.nullable is False
    assert public_id_column.unique is True


def test_public_id_default_generates_ulid() -> None:
    entity = ExamplePublicEntity(
        name="Teszt entitás",
    )

    assert entity.public_id is None

    default_function = (
        ExamplePublicEntity.__table__
        .columns["public_id"]
        .default.arg
    )

    generated = default_function(None)

    assert isinstance(generated, str)
    assert len(generated) == 26
