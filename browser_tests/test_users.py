import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Literal


class MissingBrowserTestUserEnvVarsException(Exception):
    pass


class UserType(Enum):
    DEFAULT = ""
    ACCESSIBILITY = "ACCESSIBILITY_"


AttributeType = Literal["email", "password"]


@dataclass(frozen=True)
class BrowserTestUser:
    email: str
    password: str


def _get_env_vars(attribute_type: AttributeType, user_type: UserType) -> List[str]:
    env_vars = [f"BROWSER_TEST_{user_type.value}USER_{attribute_type.upper()}"]

    # Accessibility user can use the default browser user if not defined
    if user_type is UserType.ACCESSIBILITY:
        env_vars.append(f"BROWSER_TEST_USER_{attribute_type.upper()}")

    return env_vars


def _get_env_value(attribute_type: AttributeType, user_type: UserType) -> str | None:
    for env_var in _get_env_vars(attribute_type, user_type):
        if value := os.environ.get(env_var):
            return value

    return None


def _missing_env_message(
    attribute: AttributeType,
    user_type: UserType,
) -> str:
    return f"Must define one of {', '.join(_get_env_vars(attribute, user_type))}"


def create_browser_test_user(user_type: UserType) -> BrowserTestUser:
    email = _get_env_value("email", user_type)
    password = _get_env_value("password", user_type)

    missing = []

    if email is None:
        missing.append(_missing_env_message("email", user_type))

    if password is None:
        missing.append(_missing_env_message("password", user_type))

    if missing:
        raise MissingBrowserTestUserEnvVarsException(
            f"Missing environment variables: {'; '.join(missing)}"
        )

    assert email is not None
    assert password is not None

    return BrowserTestUser(email=email, password=password)
