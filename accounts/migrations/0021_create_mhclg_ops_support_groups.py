from django.db import migrations

from accounts.enums import GroupType

ops_group_names = [
    ("mhclg_ops", GroupType.MHCLG),
    ("home_office_ops", GroupType.HOME_OFFICE),
    ("service_support", GroupType.SERVICE_SUPPORT),
]


def create_ops_groups(apps, schema_editor):
    for group_name, group_type in ops_group_names:
        Group = apps.get_model("auth", "Group")
        GroupInfo = apps.get_model("accounts", "GroupInfo")

        group = Group.objects.create(name=group_name)
        GroupInfo.objects.create(group=group, group_type=group_type)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0020_groupinfo_group_type")]

    operations = [
        migrations.RunPython(create_ops_groups),
    ]
