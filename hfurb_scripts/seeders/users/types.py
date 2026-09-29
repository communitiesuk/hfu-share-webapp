from typing import Literal, NamedTuple

AttributeType = Literal["email", "password"]


class UserToCreate(NamedTuple):
    email: str
    group_name: str
