from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0007_rename_columns_to_match_foundry"),
    ]

    operations = [
        migrations.RunSQL(
            """
          create or replace view ops_safeguarding_investigation as
          select ar.id,
                 ar.title,
                 true active_safeguarding_notifications,
                 array_agg(sn.rule_name) alert_types,
                 array(select visa_status from ontology_mvperson p where p.id in (select unnest(ar.person_id))) visa_statuses,
                 array_remove(array_agg(sn.escalation_status), null) escalation_statuses,
                 null deferral_status,
                 array_remove(array_agg(sn.assigned), null) assignees,
                 max(sn.created_at) last_created_at
          from ontology_mvaccommodationrequest ar
                   join ontology_safeguardingnotification sn on sn.ar_id = ar.id
          group by ar.id, ar.title;
          """
        ),
    ]
