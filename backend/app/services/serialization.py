from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
