from django.db import migrations


def remove_cumbria_utla(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    GroupInfo = apps.get_model("accounts", "GroupInfo")
    GroupInfo.objects.filter(utla_name="Cumbria").delete()
    Group.objects.filter(name="utla_cumbria").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0027_update_utla_cumbria_split"),
    ]

    operations = [
        migrations.RunPython(remove_cumbria_utla),
    ]
