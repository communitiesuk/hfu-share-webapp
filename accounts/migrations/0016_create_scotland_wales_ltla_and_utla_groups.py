from django.db import migrations

ltla_data = [
    ("S12000033", "Aberdeen City"),
    ("S12000034", "Aberdeenshire"),
    ("S12000041", "Angus"),
    ("S12000020", "Moray"),
    ("N09000003", "Belfast"),
    ("N09000001", "Antrim and Newtownabbey"),
    ("N09000007", "Lisburn and Castlereagh"),
    ("N09000011", "Ards and North Down"),
    ("N09000010", "Newry, Mourne and Down"),
    ("N09000002", "Armagh City, Banbridge and Craigavon"),
    ("N09000008", "Mid and East Antrim"),
    ("N09000009", "Mid Ulster"),
    ("N09000004", "Causeway Coast and Glens"),
    ("N09000005", "Derry City and Strabane"),
    ("N09000006", "Fermanagh and Omagh"),
    ("S12000042", "Dundee City"),
    ("S12000048", "Perth and Kinross"),
    ("S12000047", "Fife"),
    ("S12000006", "Dumfries and Galloway"),
    ("S12000028", "South Ayrshire"),
    ("S12000036", "City of Edinburgh"),
    ("S12000019", "Midlothian"),
    ("S12000010", "East Lothian"),
    ("S12000026", "Scottish Borders"),
    ("S12000040", "West Lothian"),
    ("S12000029", "South Lanarkshire"),
    ("S12000050", "North Lanarkshire"),
    ("S12000014", "Falkirk"),
    ("S12000005", "Clackmannanshire"),
    ("S12000030", "Stirling"),
    ("S12000049", "Glasgow City"),
    ("S12000039", "West Dunbartonshire"),
    ("S12000045", "East Dunbartonshire"),
    ("S12000011", "East Renfrewshire"),
    ("S12000038", "Renfrewshire"),
    ("S12000008", "East Ayrshire"),
    ("S12000021", "North Ayrshire"),
    ("S12000035", "Argyll and Bute"),
    ("S12000013", "Na h-Eileanan Siar"),
    ("S12000017", "Highland"),
    ("S12000023", "Orkney Islands"),
    ("S12000018", "Inverclyde"),
    ("S12000027", "Shetland Islands"),
]

utla_data = [
    ("N09000003", "Belfast", ["N09000003"]),
    ("N09000001", "Antrim and Newtownabbey", ["N09000001"]),
    ("N09000007", "Lisburn and Castlereagh", ["N09000007"]),
    ("N09000011", "Ards and North Down", ["N09000011"]),
    ("N09000010", "Newry, Mourne and Down", ["N09000010"]),
    ("N09000002", "Armagh City, Banbridge and Craigavon", ["N09000002"]),
    ("N09000008", "Mid and East Antrim", ["N09000008"]),
    ("N09000009", "Mid Ulster", ["N09000009"]),
    ("N09000004", "Causeway Coast and Glens", ["N09000004"]),
    ("N09000005", "Derry City and Strabane", ["N09000005"]),
    ("N09000006", "Fermanagh and Omagh", ["N09000006"]),
]


def create_ltla_group(ltla_name: str, gss_code: str, apps):
    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")

    group_name = "_".join(["ltla"] + ltla_name.lower().split())

    group = Group.objects.create(name=group_name)
    GroupInfo.objects.create(gss_code=gss_code, ltla_name=ltla_name, group=group)


def create_ltla_groups(apps, schema_editor):
    for ltla in ltla_data:
        gss_code, name = ltla
        create_ltla_group(name, gss_code, apps)


def create_utla_group(utla_name: str, utla_gss_code: str, ltla_gss_codes: list, apps):
    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")

    group_name = "_".join(["utla"] + utla_name.lower().split())

    group = Group.objects.create(name=group_name)
    utla_groupinfo_obj = GroupInfo.objects.create(
        utla_gss_code=utla_gss_code, utla_name=utla_name, is_utla=True, group=group
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
        ("accounts", "0015_rename_local_authority_accessrequest_group_info_and_more")
    ]

    operations = [
        migrations.RunPython(create_ltla_groups),
        migrations.RunPython(create_utla_groups),
    ]
