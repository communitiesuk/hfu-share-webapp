from django.db import migrations

utla_data = [
    (
        "E06000064",
        "Westmorland and Furness",
        ["E07000027", "E07000030", "E07000031"],
    ),
    ("E06000063", "Cumberland", ["E07000026", "E07000028", "E07000029"]),
]


def create_utla_group(utla_name: str, utla_gss_code: str, ltla_gss_codes: list, apps):
    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")

    group_name = "_".join(["utla"] + utla_name.lower().split())

    group = Group.objects.create(name=group_name)

    england_groupinfo = GroupInfo.objects.get(is_da=True, da_gss_code="E92000001")

    utla_groupinfo_obj = GroupInfo.objects.create(
        utla_gss_code=utla_gss_code,
        utla_name=utla_name,
        is_utla=True,
        group=group,
        da_name=england_groupinfo.da_name,
        da_gss_code=england_groupinfo.da_gss_code,
        parent_da_id=england_groupinfo.id,
        group_type="LOCAL_AUTHORITY",
    )

    # updates all existing LTLAs
    ltla_group_infos = GroupInfo.objects.filter(gss_code__in=ltla_gss_codes)

    ltla_group_infos.update(
        utla_gss_code=utla_gss_code,
        utla_name=utla_name,
        parent_utla=utla_groupinfo_obj,
        is_utla=False,
    )


def create_utla_groups(apps, schema_editor):
    for utla in utla_data:
        utla_gss_code, utla_name, ltla_list = utla
        create_utla_group(utla_name, utla_gss_code, ltla_list, apps)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0026_alter_user_first_name_alter_user_last_name"),
    ]

    operations = [
        migrations.RunPython(create_utla_groups),
    ]
