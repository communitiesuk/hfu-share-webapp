from django.db import migrations


def simplify_all_temp_accomm_names(apps, schema_editor):
    MvAccommodation = apps.get_model("ontology", "MvAccommodation")

    temporary_accommodations = list(
        MvAccommodation.objects.filter(
            full_address__contains="(Other) - [Local Authority]"
        )
    )

    for accommodation in temporary_accommodations:
        accommodation.full_address = accommodation.full_address.replace(
            "(Other) - [Local Authority]", "-"
        ).strip()
        accommodation.save()


class Migration(migrations.Migration):
    dependencies = [
        (
            "ontology",
            "0037_merge_20250618_1023",
        ),
    ]

    operations = [migrations.RunPython(simplify_all_temp_accomm_names)]
