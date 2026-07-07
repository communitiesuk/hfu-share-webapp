from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0026_alter_devcheckv2_check_status"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE ontology_devcheckv2_accommodation_id RENAME TO ontology_devcheckv2_accommodation;",
            reverse_sql="ALTER TABLE ontology_devcheckv2_accommodation RENAME TO ontology_devcheckv2_accommodation_id;",
        ),
        migrations.RunSQL(
            sql='ALTER TABLE "ontology_devcheckv2_AR_id" RENAME TO "ontology_devcheckv2_AR";',
            reverse_sql='ALTER TABLE "ontology_devcheckv2_AR" RENAME TO "ontology_devcheckv2_AR_id";',
        ),
        migrations.RunSQL(
            sql="ALTER TABLE ontology_devcheckv2_eoi_host_id RENAME TO ontology_devcheckv2_eoi_host;",
            reverse_sql="ALTER TABLE ontology_devcheckv2_eoi_host RENAME TO ontology_devcheckv2_eoi_host_id;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE ontology_devcheckv2_group_id RENAME TO ontology_devcheckv2_group;",
            reverse_sql="ALTER TABLE ontology_devcheckv2_group RENAME TO ontology_devcheckv2_group_id;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE ontology_devcheckv2_person_id RENAME TO ontology_devcheckv2_person;",
            reverse_sql="ALTER TABLE ontology_devcheckv2_person RENAME TO ontology_devcheckv2_person_id;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE ontology_devcheckv2_sponsor_id RENAME TO ontology_devcheckv2_sponsor;",
            reverse_sql="ALTER TABLE ontology_devcheckv2_sponsor RENAME TO ontology_devcheckv2_sponsor_id;",
        ),
    ]
