from django.db import migrations

from accounts.enums import GroupType


def create_early_access_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")

    early_access_types = [
        GroupType.LOCAL_AUTHORITY_EARLY_ADOPTERS,
        GroupType.DEVOLVED_ADMINISTRATION_EARLY_ADOPTERS,
        GroupType.HOME_OFFICE_EARLY_ADOPTERS,
        GroupType.MHCLG_EARLY_ADOPTERS,
        GroupType.SERVICE_SUPPORT_EARLY_ADOPTERS,
    ]

    for group_type in early_access_types:
        group_name = f"{group_type.name.lower()}"
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            groupinfo = GroupInfo.objects.create(
                group=group,
                group_type=group_type,
            )
            groupinfo.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0031_alter_accessrequest_group_type_and_more"),
    ]

    operations = [
        migrations.RunPython(create_early_access_groups),
    ]
