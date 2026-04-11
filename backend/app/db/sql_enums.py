from __future__ import annotations

from enum import Enum as PyEnum

from sqlalchemy import Enum as SAEnum


def pg_enum(enum_cls: type[PyEnum], name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda enum_type: [item.value for item in enum_type],
        validate_strings=True,
        native_enum=True,
    )
