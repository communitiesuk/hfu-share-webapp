from django.db import migrations, models


def correct_reviewed_at(apps, schema_editor):
    AccessRequests = apps.get_model("accounts", "AccessRequest")
    for req in AccessRequests.objects.all():
        if req.status == "PENDING":
            req.reviewed_at = None
            req.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0022_accessrequest_hidden_by_requester"),
    ]

    operations = [
        migrations.RenameField(
            model_name="accessrequest",
            old_name="updated_at",
            new_name="reviewed_at",
        ),
        migrations.AlterField(
            model_name="accessrequest",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(correct_reviewed_at),
    ]
