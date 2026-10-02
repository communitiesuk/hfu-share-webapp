from typing import cast

from django.contrib.auth.models import Group

from accounts.enums import (
    BROWSER_TEST_FIRST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    BROWSER_TEST_SECOND_LA_GROUP_NAME,
    BROWSER_TEST_UTLA_NAME,
    GroupType,
)
from accounts.tests.factories import GroupFactory


def create_browser_test_la_groups() -> list[Group]:
    return [
        cast(
            Group,
            GroupFactory(
                name=name,
                groupinfo__ltla_name=ltla_name,
                groupinfo__utla_name=BROWSER_TEST_UTLA_NAME,
                groupinfo__da_name="England",
                groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
            ),
        )
        for name, ltla_name in (
            (BROWSER_TEST_FIRST_LA_GROUP_NAME, BROWSER_TEST_LTLA_NAMES[0]),
            (BROWSER_TEST_SECOND_LA_GROUP_NAME, BROWSER_TEST_LTLA_NAMES[1]),
        )
    ]
