from django.conf import settings
from django.db import migrations

from accounts.enums import (
    BROWSER_TEST_LTLA_NAMES,
    BROWSER_TEST_SECOND_LA_GROUP_NAME,
    BROWSER_TEST_UTLA_GROUP_NAME,
    BROWSER_TEST_UTLA_NAME,
    GroupType,
)


def environment_allows_browser_test_groups() -> bool:
    return settings.ENVIRONMENT == "dev" or settings.DEBUG


def create_second_browser_test_la_group(apps, schema_editor):
    if not environment_allows_browser_test_groups():
        return

    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")

    utla_group_info = GroupInfo.objects.filter(
        group__name=BROWSER_TEST_UTLA_GROUP_NAME
    ).first()

    ltla_group, ltla_created = Group.objects.get_or_create(
        name=BROWSER_TEST_SECOND_LA_GROUP_NAME
    )
    if ltla_created:
        GroupInfo.objects.create(
            group=ltla_group,
            group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
            ltla_name=BROWSER_TEST_LTLA_NAMES[1],
            gss_code="E99999997",
            utla_name=BROWSER_TEST_UTLA_NAME,
            parent_utla=utla_group_info,
            da_name="England",
            description="Second browser test local authority, dev environments only",
        )


def delete_second_browser_test_la_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=BROWSER_TEST_SECOND_LA_GROUP_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0034_create_browser_test_la_group"),
    ]

    operations = [
        migrations.RunPython(
            create_second_browser_test_la_group, delete_second_browser_test_la_group
        ),
    ]
