import os
from typing import cast

import pytest

USER_TYPES = ("default",)


class BrowserTestUser:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password


class BrowserTestUserFactory:
    @staticmethod
    def create(user_type: str) -> BrowserTestUser:
        user_type_param = f"{user_type.upper()}_" if user_type != "default" else ""

        required_params = [
            f"BROWSER_TEST_{user_type_param}USER_EMAIL",
            f"BROWSER_TEST_{user_type_param}USER_PASSWORD",
        ]

        missing = [param for param in required_params if not os.getenv(param)]

        if missing:
            pytest.exit(
                f"Missing environment variables: {', '.join(missing)}",
                returncode=1,
            )

        return BrowserTestUser(
            email=cast(
                str, os.environ.get(f"BROWSER_TEST_{user_type_param}USER_EMAIL")
            ),
            password=cast(
                str, os.environ.get(f"BROWSER_TEST_{user_type_param}USER_PASSWORD")
            ),
        )
