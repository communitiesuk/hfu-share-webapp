from typing import List

from .types import UserToCreate

CUSTOM_USERS_TO_CREATE: List[UserToCreate] = [
    UserToCreate(
        "mhclg_ops@example.com",
        "mhclg_ops",
    ),
    UserToCreate(
        "home_office_ops@example.com",
        "home_office_ops",
    ),
    UserToCreate(
        "service_support@example.com",
        "service_support",
    ),
    UserToCreate(
        "da@example.com",
        "devolved_administration",
    ),
    UserToCreate(
        "croydon@example.com",
        "croydon",
    ),
    UserToCreate(
        "bromley@example.com",
        "ltla_bromley",
    ),
    UserToCreate(
        "lewisham@example.com",
        "ltla_lewisham",
    ),
]
