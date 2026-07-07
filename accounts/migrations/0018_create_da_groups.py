from django.db import migrations

da_data = [
    ("E92000001", "England"),
    ("N92000002", "Northern Ireland"),
    ("S92000003", "Scotland"),
    ("W92000004", "Wales"),
]


def create_da_group(da_name: str, da_gss_code: str, apps):
    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")

    group_name = "_".join(["da"] + da_name.lower().split())

    group = Group.objects.create(name=group_name)
    da_groupinfo_obj = GroupInfo.objects.create(
        da_gss_code=da_gss_code, da_name=da_name, is_da=True, group=group
    )

    gss_code_prefix = da_gss_code[0]

    utla_ltla_group_infos = GroupInfo.objects.filter(
        gss_code__startswith=gss_code_prefix
    ) | GroupInfo.objects.filter(utla_gss_code__startswith=gss_code_prefix)

    utla_ltla_group_infos.update(
        da_gss_code=da_gss_code,
        da_name=da_name,
        parent_da=da_groupinfo_obj,
        is_da=False,
    )


def create_da_groups(apps, schema_editor):
    for da in da_data:
        da_gss_code, da_name = da
        create_da_group(da_name, da_gss_code, apps)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_groupinfo_da_gss_code_groupinfo_da_name_and_more")
    ]

    operations = [
        migrations.RunPython(create_da_groups),
    ]
