from django.db import migrations

check_types = [
    {
        "id": "1",
        "check_name": "Residential Accommodation Exists",
        "check_description": "I have checked the accommodation exists and can be used as residential accommodation.",
        "active": True,
        "is_uam": False,
        "linked_object": "accommodation",
        "pre_arrival": True,
    },
    {
        "id": "2",
        "check_name": "Accommodation Visited & Suitable",
        "check_description": "I have visited the accommodation and it appears suitable for the proposed guests.",
        "active": True,
        "is_uam": False,
        "linked_object": "accommodation",
        "pre_arrival": True,
    },
    {
        "id": "3",
        "check_name": "DBS Checks",
        "check_description": "I have run DBS checks for the people living in this accommodation.",
        "active": True,
        "is_uam": False,
        "linked_object": "sponsor",
        "pre_arrival": True,
    },
    {
        "id": "4",
        "check_name": "Group Arrived in Accommodation",
        "check_description": "I have confirmed that the guest(s) has/have arrived in the accommodation.",
        "active": True,
        "is_uam": False,
        "linked_object": "group",
        "pre_arrival": False,
    },
    {
        "id": "5",
        "check_name": "Safeguarding Checks Complete",
        "check_description": "I have completed safeguarding checks, including visiting the guests in their accommodation and can confirm there are no serious safeguarding concerns.",
        "active": True,
        "is_uam": False,
        "linked_object": "group",
        "pre_arrival": False,
    },
    {
        "id": "6",
        "check_name": "DBS Checks",
        "check_description": "I have run DBS checks for the people living in this accommodation.",
        "active": True,
        "is_uam": False,
        "linked_object": "eoi_host",
        "pre_arrival": True,
    },
    {
        "id": "7",
        "check_name": "Sponsor Accepts Role and Expectations",
        "check_description": "I have contacted the sponsor and have discussed their role and expectations of them including duration of the sponsorship agreement, meeting the child’s day to day needs, financial responsibility for the child, staying in touch with their parent(s) legal guardian.",
        "active": True,
        "is_uam": True,
        "linked_object": "sponsor",
        "pre_arrival": True,
    },
    {
        "id": "8",
        "check_name": "Sponsor Arrangements Suitable",
        "check_description": "I have carried out a social work led assessment to confirm the arrangements are suitable.",
        "active": True,
        "is_uam": True,
        "linked_object": "sponsor",
        "pre_arrival": True,
    },
    {
        "id": "9",
        "check_name": "UK Form Uploaded",
        "check_description": "The Home Office have uploaded the UK form for this eligible child.",
        "active": True,
        "is_uam": True,
        "linked_object": "person",
        "pre_arrival": True,
    },
    {
        "id": "10",
        "check_name": "Ukraine Form Uploaded",
        "check_description": "The Home Office have uploaded the Ukraine form for this eligible child.",
        "active": True,
        "is_uam": True,
        "linked_object": "person",
        "pre_arrival": True,
    },
    {
        "id": "11",
        "check_name": "Home Office Security Checks on Household",
        "check_description": "The Home Office have completed security checks on relevant household members.",
        "active": True,
        "is_uam": True,
        "linked_object": "accommodation",
        "pre_arrival": True,
    },
    {
        "id": "12",
        "check_name": "Home Office Security Checks on Sponsor",
        "check_description": "The Home Office have completed security checks on the sponsor.",
        "active": True,
        "is_uam": True,
        "linked_object": "sponsor",
        "pre_arrival": True,
    },
]


def populate_checktypes(apps, schema_editor):
    CheckType = apps.get_model("ontology", "CheckType")

    for check in check_types:
        CheckType.objects.update_or_create(**check)


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0028_alter_checktype_id"),
    ]

    operations = [
        migrations.RunPython(populate_checktypes),
    ]
