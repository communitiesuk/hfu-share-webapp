from django.db import migrations, models

GROUP_TYPE_CHOICES = [
    ("DEV", "Dev"),
    ("LOCAL_AUTHORITY", "Local authority"),
    (
        "LOCAL_AUTHORITY_EARLY_ADOPTERS",
        "Early adopters - Local authority",
    ),
    (
        "LOCAL_AUTHORITY_BROWSER_TEST",
        "Browser test - Local authority",
    ),
    ("DEVOLVED_ADMINISTRATION", "Devolved administration"),
    (
        "DEVOLVED_ADMINISTRATION_EARLY_ADOPTERS",
        "Early adopters - Devolved administration",
    ),
    ("HOME_OFFICE", "Home Office operations team"),
    (
        "HOME_OFFICE_EARLY_ADOPTERS",
        "Early adopters - Home Office operations team",
    ),
    ("MHCLG", "MHCLG operations team"),
    ("MHCLG_EARLY_ADOPTERS", "Early adopters - MHCLG operations team"),
    ("SERVICE_SUPPORT", "Service support"),
    (
        "SERVICE_SUPPORT_EARLY_ADOPTERS",
        "Early adopters - Service support",
    ),
]


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0032_create_early_access_groups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessrequest",
            name="group_type",
            field=models.TextField(choices=GROUP_TYPE_CHOICES),
        ),
        migrations.AlterField(
            model_name="groupinfo",
            name="group_type",
            field=models.TextField(choices=GROUP_TYPE_CHOICES),
        ),
    ]
