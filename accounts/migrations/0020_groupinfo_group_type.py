from django.db import migrations, models


def set_group_type(apps, schema_editor):
    GroupInfo = apps.get_model("accounts", "GroupInfo")
    for obj in GroupInfo.objects.all():
        if obj.group.name == "dev":
            obj.group_type = "DEV"
        elif obj.is_da:
            obj.group_type = "DEVOLVED_ADMINISTRATION"
        else:
            obj.group_type = "LOCAL_AUTHORITY"
        obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0019_accessrequest_da_group_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessrequest",
            name="group_type",
            field=models.TextField(
                choices=[
                    ("DEV", "Dev"),
                    ("LOCAL_AUTHORITY", "Local authority"),
                    ("DEVOLVED_ADMINISTRATION", "Devolved administration"),
                    ("MHCLG", "MHCLG operations team"),
                    ("HOME_OFFICE", "Home office operations team"),
                    ("SERVICE_SUPPORT", "Service support"),
                ]
            ),
        ),
        migrations.AddField(
            model_name="groupinfo",
            name="group_type",
            field=models.TextField(
                choices=[
                    ("DEV", "Dev"),
                    ("LOCAL_AUTHORITY", "Local authority"),
                    ("DEVOLVED_ADMINISTRATION", "Devolved administration"),
                    ("MHCLG", "MHCLG operations team"),
                    ("HOME_OFFICE", "Home office operations team"),
                    ("SERVICE_SUPPORT", "Service support"),
                ],
                default="LOCAL_AUTHORITY",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_group_type),
    ]
