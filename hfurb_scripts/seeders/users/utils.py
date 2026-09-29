import os
from typing import List

from accounts.enums import BROWSER_TEST_FIRST_LA_GROUP_NAME

from .enums import UserType
from .exceptions import MissingBrowserTestUserEnvVarsException
from .models import BrowserTestUser
from .types import AttributeType


def _get_browser_test_credentials_env_var_names(
    attribute_type: AttributeType, user_type: UserType
) -> List[str]:
    env_vars = [f"BROWSER_TEST_{user_type.value}USER_{attribute_type.upper()}"]

    # Accessibility user can use the default browser user if not defined
    if user_type is UserType.ACCESSIBILITY:
        env_vars.append(f"BROWSER_TEST_USER_{attribute_type.upper()}")

    return env_vars


def _get_browser_test_credential_from_env_vars(
    attribute_type: AttributeType, user_type: UserType
) -> str | None:
    for env_var in _get_browser_test_credentials_env_var_names(
        attribute_type, user_type
    ):
        if value := os.environ.get(env_var):
            return value

    return None


def _missing_env_variable_message(
    attribute: AttributeType,
    user_type: UserType,
) -> str:
    return (
        "Must define one of "
        f"{
            ', '.join(_get_browser_test_credentials_env_var_names(attribute, user_type))
        }"
    )


def build_browser_test_user(user_type: UserType) -> BrowserTestUser:
    email = _get_browser_test_credential_from_env_vars("email", user_type)
    password = _get_browser_test_credential_from_env_vars("password", user_type)

    missing = []

    if email is None:
        missing.append(_missing_env_variable_message("email", user_type))

    if password is None:
        missing.append(_missing_env_variable_message("password", user_type))

    if missing:
        raise MissingBrowserTestUserEnvVarsException(
            f"Missing environment variables: {'; '.join(missing)}"
        )

    assert email is not None
    assert password is not None

    return BrowserTestUser(
        email=email, group_name=BROWSER_TEST_FIRST_LA_GROUP_NAME, password=password
    )
