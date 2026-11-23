from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class LinkedRecordData:
    """Values to construct a link to the object's details page."""

    view_name: str
    id: Any
    title: str
    status_type: str | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        self.title = self.title or "Unknown"


def get_full_name(
    first_name: str | None, family_name: str | None, default_value: str | T = "Unknown"
) -> str | T:
    name = f"{first_name or ''} {family_name or ''}".strip()
    return name or default_value
