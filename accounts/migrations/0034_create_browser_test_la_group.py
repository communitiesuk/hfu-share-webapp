from django.conf import settings
from django.db import migrations

from accounts.enums import (
    BROWSER_TEST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    BROWSER_TEST_UTLA_GROUP_NAME,
    BROWSER_TEST_UTLA_NAME,
    GroupType,
)


def environment_allows_browser_test_groups() -> bool:
    return settings.ENVIRONMENT == "dev" or settings.DEBUG


def create_browser_test_la_groups(apps, schema_editor):
    if not environment_allows_browser_test_groups():
        return

    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")

    utla_group, utla_created = Group.objects.get_or_create(
        name=BROWSER_TEST_UTLA_GROUP_NAME
    )
    utla_group_info = None
    if utla_created:
        utla_group_info = GroupInfo.objects.create(
            group=utla_group,
            group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
            utla_name=BROWSER_TEST_UTLA_NAME,
            utla_gss_code="E99999998",
            is_utla=True,
            da_name="England",
            description="Browser test upper tier authority, dev environments only",
        )

    ltla_group, ltla_created = Group.objects.get_or_create(
        name=BROWSER_TEST_LA_GROUP_NAME
    )
    if ltla_created:
        GroupInfo.objects.create(
            group=ltla_group,
            group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
            ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            gss_code="E99999999",
            utla_name=BROWSER_TEST_UTLA_NAME,
            parent_utla=utla_group_info,
            da_name="England",
            description="Browser test local authority, dev environments only",
        )


def delete_browser_test_la_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=[BROWSER_TEST_LA_GROUP_NAME, BROWSER_TEST_UTLA_GROUP_NAME]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0033_alter_accessrequest_group_type_and_more"),
    ]

    operations = [
        migrations.RunPython(
            create_browser_test_la_groups, delete_browser_test_la_groups
        ),
    ]
