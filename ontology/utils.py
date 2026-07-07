from dataclasses import dataclass
from typing import Any


@dataclass
class LinkedRecordData:
    """Values to construct a link to the object's details page."""

    view_name: str
    id: Any
    title: str
    status_type: str | None = None
    status: str | None = None
