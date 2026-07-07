from typing import Self

from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.db.models.expressions import OuterRef

from ontology.mixins import LocalAuthorityPermissionsManagerMixin


class ExportToolObjectQuerySet(models.QuerySet):
    def with_sponsor_las(self) -> Self:
        from ontology.models import MvVolunteer

        sponsor_ltla_name = ArraySubquery(
            MvVolunteer.objects.filter(
                id=OuterRef("sponsor_id"), accommodations__ltla_name__isnull=False
            )
            .values("accommodations__ltla_name")
            .distinct()
        )

        sponsor_utla_name = ArraySubquery(
            MvVolunteer.objects.filter(
                id=OuterRef("sponsor_id"), accommodations__utla_name__isnull=False
            )
            .values("accommodations__utla_name")
            .distinct()
        )
        return self.annotate(
            sponsor_ltla_name=sponsor_ltla_name,
            sponsor_utla_name=sponsor_utla_name,
        )

    def with_rematched_host_las(self) -> Self:
        from ontology.models import MvVolunteer

        rematched_host_ltla_name = ArraySubquery(
            MvVolunteer.objects.filter(
                id=OuterRef("rematched_host_id"),
                accommodations__ltla_name__isnull=False,
            )
            .values("accommodations__ltla_name")
            .distinct()
        )

        rematched_host_utla_name = ArraySubquery(
            MvVolunteer.objects.filter(
                id=OuterRef("rematched_host_id"),
                accommodations__utla_name__isnull=False,
            )
            .values("accommodations__utla_name")
            .distinct()
        )
        return self.annotate(
            rematched_host_ltla_name=rematched_host_ltla_name,
            rematched_host_utla_name=rematched_host_utla_name,
        )

    def with_accommodation_las(self) -> Self:
        from ontology.models import MvAccommodation

        accommodation_ltla_name = ArraySubquery(
            MvAccommodation.objects.filter(
                id=OuterRef("accommodation_id"), ltla_name__isnull=False
            )
            .values("ltla_name")
            .distinct()
        )

        accommodation_utla_name = ArraySubquery(
            MvAccommodation.objects.filter(
                id=OuterRef("accommodation_id"), utla_name__isnull=False
            )
            .values("utla_name")
            .distinct()
        )

        return self.annotate(
            accommodation_ltla_name=accommodation_ltla_name,
            accommodation_utla_name=accommodation_utla_name,
        )


class ExportToolObjectManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def get_queryset(self):
        return (
            ExportToolObjectQuerySet(self.model, using=self._db)
            .with_sponsor_las()
            .with_accommodation_las()
            .with_rematched_host_las()
        )

    def get_queryset_without_annotations(self):
        return ExportToolObjectQuerySet(self.model, using=self._db)

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(ltla_name__overlap=ltla_names)

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(utla_name__overlap=utla_names)

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class ExportToolObject(models.Model):
    objects = ExportToolObjectManager()

    accommodation_accommodation_provider_type = models.TextField(
        null=True, blank=True, db_column="accommodation_accommodation_provider_type"
    )
    accommodation_full_address = models.TextField(
        null=True, blank=True, db_column="accommodation_full_address"
    )
    accommodation_id = models.TextField(
        null=True, blank=True, db_column="accommodation_id"
    )
    accommodation_local_authority = models.TextField(
        null=True, blank=True, db_column="accommodation_local_authority"
    )
    accommodation_postcode = models.TextField(
        null=True, blank=True, db_column="accommodation_postcode"
    )
    accommodation_submission_guid = models.TextField(
        null=True, blank=True, db_column="accommodation_submission_guid"
    )
    accommodation_volunteer_id = models.TextField(
        null=True, blank=True, db_column="accommodation_volunteer_id"
    )
    case_left_programme_reason = models.TextField(
        null=True, blank=True, db_column="case_left_programme_reason"
    )
    central_case_flag = models.BooleanField(
        null=True, blank=True, db_column="central_case_flag"
    )
    checks_status = models.TextField(null=True, blank=True, db_column="checks_status")
    comment = models.TextField(null=True, blank=True, db_column="comment")
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    date_from = models.DateField(null=True, blank=True, db_column="date_from")
    expected_end_date = models.DateField(
        null=True, blank=True, db_column="expected_end_date"
    )
    expected_end_date_is_autogenerated = models.BooleanField(
        null=True, blank=True, db_column="expected_end_date_is_autogenerated"
    )
    export_tool_id = models.TextField(primary_key=True, db_column="export_tool_id")
    group_date_of_arrival = models.DateField(
        null=True, blank=True, db_column="group_date_of_arrival"
    )
    group_id = models.TextField(null=True, blank=True, db_column="group_id")
    group_max_age = models.IntegerField(
        null=True, blank=True, db_column="group_max_age"
    )
    group_merged_group = models.TextField(
        null=True, blank=True, db_column="group_merged_group"
    )
    group_min_age = models.IntegerField(
        null=True, blank=True, db_column="group_min_age"
    )
    group_number_of_people_in_group = models.BigIntegerField(
        null=True, blank=True, db_column="group_number_of_people_in_group"
    )
    group_primary_contact_can_be_contacted_by_phone = models.TextField(
        null=True,
        blank=True,
        db_column="group_primary_contact_can_be_contacted_by_phone",
    )
    group_primary_contact_email = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="group_primary_contact_email",
    )
    group_primary_contact_email_after_decision = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="group_primary_contact_email_after_decision",
    )
    group_primary_contact_email_for_decision = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="group_primary_contact_email_for_decision",
    )
    group_primary_contact_email_for_questions = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="group_primary_contact_email_for_questions",
    )
    group_primary_contact_first_name = models.TextField(
        null=True, blank=True, db_column="group_primary_contact_first_name"
    )
    group_primary_contact_last_name = models.TextField(
        null=True, blank=True, db_column="group_primary_contact_last_name"
    )
    group_primary_contact_phone = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="group_primary_contact_phone",
    )
    group_title = models.TextField(null=True, blank=True, db_column="group_title")
    hash = models.TextField(null=True, blank=True, db_column="hash")
    id = models.TextField(null=True, blank=True, db_column="id")
    is_multi_la = models.BooleanField(null=True, blank=True, db_column="is_multi_la")
    last_updated = models.DateTimeField(null=True, blank=True, db_column="last_updated")
    latest_application_date = models.DateField(
        null=True, blank=True, db_column="latest_application_date"
    )
    ltla_name = ArrayField(
        models.TextField(), null=True, blank=True, db_column="ltla_name"
    )
    number_of_people = models.BigIntegerField(
        null=True, blank=True, db_column="number_of_people"
    )
    person_latest_arrival_date = models.DateField(
        null=True, blank=True, db_column="person_latest_arrival_date"
    )
    person_age = models.BigIntegerField(null=True, blank=True, db_column="person_age")
    person_application_number = ArrayField(
        models.TextField(), null=True, blank=True, db_column="person_application_number"
    )
    person_arrival_date = models.DateField(
        null=True, blank=True, db_column="person_arrival_date"
    )
    person_can_be_contacted_by_phone = models.TextField(
        null=True, blank=True, db_column="person_can_be_contacted_by_phone"
    )
    person_date_of_birth = models.DateField(
        null=True, blank=True, db_column="person_date_of_birth"
    )
    person_earliest_issued_visa_decision_date = models.DateField(
        null=True, blank=True, db_column="person_earliest_issued_visa_decision_date"
    )
    person_email = ArrayField(
        models.TextField(), null=True, blank=True, db_column="person_email"
    )
    person_email_after_decision = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="person_email_after_decision",
    )
    person_email_for_decision = ArrayField(
        models.TextField(), null=True, blank=True, db_column="person_email_for_decision"
    )
    person_email_for_questions = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="person_email_for_questions",
    )
    person_full_name = models.TextField(
        null=True, blank=True, db_column="person_full_name"
    )
    person_gender = models.TextField(null=True, blank=True, db_column="person_gender")
    person_group_id = models.TextField(
        null=True, blank=True, db_column="person_group_id"
    )
    person_id = models.TextField(null=True, blank=True, db_column="person_id")
    person_is_uam = models.BooleanField(
        null=True, blank=True, db_column="person_is_uam"
    )
    person_old_group_id = models.TextField(
        null=True, blank=True, db_column="person_old_group_id"
    )
    person_passport_id = ArrayField(
        models.TextField(), null=True, blank=True, db_column="person_passport_id"
    )
    person_phone = ArrayField(
        models.TextField(), null=True, blank=True, db_column="person_phone"
    )
    person_upe_visa_status = models.TextField(
        null=True, blank=True, db_column="person_upe_visa_status"
    )
    person_visa_status = models.TextField(
        null=True, blank=True, db_column="person_visa_status"
    )
    rematched_host_email = models.TextField(
        null=True, blank=True, db_column="rematched_host_email"
    )
    rematched_accommodation_request_id = models.TextField(
        null=True, blank=True, db_column="rematched_accommodation_request_id"
    )
    rematched_host_contact_number = models.TextField(
        null=True, blank=True, db_column="rematched_host_contact_number"
    )
    rematched_host_full_name = models.TextField(
        null=True, blank=True, db_column="rematched_host_full_name"
    )
    rematched_host_id = models.TextField(
        null=True, blank=True, db_column="rematched_host_id"
    )
    sponsor_adverse_hit = models.BooleanField(
        null=True, blank=True, db_column="sponsor_adverse_hit"
    )
    sponsor_age = models.IntegerField(null=True, blank=True, db_column="sponsor_age")
    sponsor_date_of_birth = models.DateField(
        null=True, blank=True, db_column="sponsor_date_of_birth"
    )
    sponsor_email = models.TextField(null=True, blank=True, db_column="sponsor_email")
    sponsor_expiry_date_id = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_expiry_date_id"
    )
    sponsor_family_situation = models.TextField(
        null=True, blank=True, db_column="sponsor_family_situation"
    )
    sponsor_full_name = models.TextField(
        null=True, blank=True, db_column="sponsor_full_name"
    )
    sponsor_has_identity_card = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_has_identity_card"
    )
    sponsor_id = models.TextField(null=True, blank=True, db_column="sponsor_id")
    sponsor_issue_date_id = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_issue_date_id"
    )
    sponsor_issuing_authority_of_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="sponsor_issuing_authority_of_id",
    )
    sponsor_national_identity_card_number = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="sponsor_national_identity_card_number",
    )
    sponsor_phone_number = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_phone_number"
    )
    sponsor_sex = models.TextField(null=True, blank=True, db_column="sponsor_sex")
    sponsor_withdrawn = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_withdrawn"
    )
    status = models.TextField(null=True, blank=True, db_column="status")
    title = models.TextField(null=True, blank=True, db_column="title")
    unique_application_number = ArrayField(
        models.TextField(), null=True, blank=True, db_column="unique_application_number"
    )
    utla_name = ArrayField(
        models.TextField(), null=True, blank=True, db_column="utla_name"
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
