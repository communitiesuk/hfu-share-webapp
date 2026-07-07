from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Count, F, ManyToManyField, Q, QuerySet

from accounts.models import User


class PersonMasterRecordManager(models.Manager):
    def get_for_user(self, user: User) -> QuerySet:
        # Filter to only persons we can see.
        user_viewable_persons = apps.get_model(
            "ontology.MvPerson", require_ready=True
        ).objects.get_for_user(user)

        pmrs = (
            self.get_queryset()
            .annotate(
                total_persons_linked=Count("persons", distinct=True),
                viewable_persons_linked=Count(
                    "persons",
                    filter=Q(persons__in=user_viewable_persons),
                    distinct=True,
                ),
            )
            .filter(total_persons_linked=F("viewable_persons_linked"))
        )

        return pmrs


class PersonMasterRecord(models.Model):
    objects = PersonMasterRecordManager()

    adverse_rematch = ArrayField(
        models.TextField(), null=True, db_column="adverse_rematch"
    )
    age = ArrayField(models.TextField(), null=True, db_column="age")
    application_number = ArrayField(
        models.TextField(), null=True, db_column="application_number"
    )
    arrival_date = ArrayField(models.TextField(), null=True, db_column="arrival_date")
    arrival_port_code = ArrayField(
        models.TextField(), null=True, db_column="arrival_port_code"
    )
    arrival_port_name = ArrayField(
        models.TextField(), null=True, db_column="arrival_port_name"
    )
    can_be_contacted_by_phone = ArrayField(
        models.TextField(), null=True, db_column="can_be_contacted_by_phone"
    )
    created_at = ArrayField(models.TextField(), null=True, db_column="created_at")
    created_by = ArrayField(models.TextField(), null=True, db_column="created_by")
    date_of_birth = ArrayField(models.TextField(), null=True, db_column="date_of_birth")
    disability_flag = ArrayField(
        models.TextField(), null=True, db_column="disability_flag"
    )
    email = ArrayField(models.TextField(), null=True, db_column="email")
    email_after_decision = ArrayField(
        models.TextField(), null=True, db_column="email_after_decision"
    )
    email_for_decision = ArrayField(
        models.TextField(), null=True, db_column="email_for_decision"
    )
    email_for_questions = ArrayField(
        models.TextField(), null=True, db_column="email_for_questions"
    )
    first_name = ArrayField(models.TextField(), null=True, db_column="first_name")
    group_id = ArrayField(models.TextField(), null=True, db_column="group_id")
    gwf = ArrayField(models.TextField(), null=True, db_column="gwf")
    id = ArrayField(models.TextField(), null=True, db_column="id")
    is_principal = ArrayField(models.TextField(), null=True, db_column="is_principal")
    is_uam = ArrayField(models.TextField(), null=True, db_column="is_uam")
    last_edited_at = ArrayField(
        models.TextField(), null=True, db_column="last_edited_at"
    )
    last_edited_by = ArrayField(
        models.TextField(), null=True, db_column="last_edited_by"
    )
    last_name = ArrayField(models.TextField(), null=True, db_column="last_name")
    nationality = ArrayField(models.TextField(), null=True, db_column="nationality")
    notional_data = ArrayField(models.TextField(), null=True, db_column="notional_data")
    old_group_id = ArrayField(models.TextField(), null=True, db_column="old_group_id")
    passport_id = ArrayField(models.TextField(), null=True, db_column="passport_id")
    phone = ArrayField(models.TextField(), null=True, db_column="phone")
    primary_application_numbers = ArrayField(
        models.TextField(), null=True, db_column="primary_application_numbers"
    )
    principal_record = models.ForeignKey(
        "ontology.MvPerson",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_column="principal_record_id",
    )
    record_id = models.TextField(primary_key=True, db_column="record_id")
    gender = ArrayField(models.TextField(), null=True, db_column="gender")
    source = ArrayField(models.TextField(), null=True, db_column="source")
    sponsorship_certification_number = ArrayField(
        models.TextField(), null=True, db_column="sponsorship_certification_number"
    )
    suggested_type = models.TextField(null=True, db_column="suggested_type")
    title = ArrayField(models.TextField(), null=True, db_column="title")
    travelling_to_uk = ArrayField(
        models.TextField(), null=True, db_column="travelling_to_uk"
    )
    type = models.TextField(null=True, db_column="type")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )
    visa_decision_date = ArrayField(
        models.TextField(), null=True, db_column="visa_decision_date"
    )
    visa_status = ArrayField(models.TextField(), null=True, db_column="visa_status")
    wheelchair_required = ArrayField(
        models.TextField(), null=True, db_column="wheelchair_required"
    )

    persons = ManyToManyField(
        "ontology.MvPerson", db_table="ontology_person_to_master_record"
    )

    def card_title(self):
        first_record = self.persons.first()
        count = self.persons.count()
        return (
            f"{first_record.get_full_name()} and "
            f"{count - 1} {'others' if count > 2 else 'other'}"
        )
