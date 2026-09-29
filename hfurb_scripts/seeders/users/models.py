from dataclasses import dataclass


@dataclass(frozen=True)
class CustomUser:
    email: str
    group_name: str
    password: str


BrowserTestUser = CustomUser
