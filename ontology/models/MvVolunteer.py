import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, QuerySet

from accounts.models import User
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models import CheckType, DevCheckV2
from ontology.models.DevCheckV2 import validate_safeguarding_status
from ontology.models.MvPerson import MvPerson
from ontology.utils import LinkedRecordData


def generate_id():
    return f"sponsor-{uuid.uuid4()}"


class MvVolunteerManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(accommodations__ltla_name__in=ltla_names)

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(accommodations__utla_name__in=utla_names)

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class MvVolunteer(models.Model):
    objects = MvVolunteerManager()
    checks: QuerySet[DevCheckV2]

    class SponsorType(models.TextChoices):
        INDIVIDUAL = ("Individual",)
        LOCAL_AUTHORITY = ("Local Authority",)
        ORG = ("Org",)

    adverse_hit = models.BooleanField(null=True, blank=True, db_column="adverse_hit")
    age = models.IntegerField(null=True, blank=True, db_column="age")
    comments = models.TextField(null=True, blank=True, db_column="comments")
    created_date = models.DateTimeField(null=True, blank=True, db_column="created_date")
    date_of_birth = models.DateField(null=True, blank=True, db_column="date_of_birth")
    email = models.TextField(null=True, blank=True, db_column="email")
    expiry_date_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="expiry_date_id",
        verbose_name="Expiry date ID",
    )
    family_situation = models.TextField(
        null=True, blank=True, db_column="family_situation"
    )
    first_name = models.TextField(null=True, blank=True, db_column="first_name")
    flag_unsuitable = models.BooleanField(
        null=True, blank=True, db_column="flag_unsuitable"
    )
    full_name = models.TextField(null=True, blank=True, db_column="full_name")
    gwf = ArrayField(
        models.TextField(), null=True, blank=True, db_column="gwf", verbose_name="GWF"
    )
    has_background_check = models.BooleanField(
        null=True, blank=True, db_column="has_background_check"
    )
    has_identity_card = ArrayField(
        models.TextField(), null=True, blank=True, db_column="has_identity_card"
    )
    hosting_duration = models.IntegerField(
        null=True, blank=True, db_column="hosting_duration"
    )
    id = models.TextField(
        primary_key=True, default=generate_id, db_column="id", verbose_name="ID"
    )
    Individual_or_Organisation = models.TextField(
        null=True, blank=True, db_column="Individual_or_Organisation"
    )
    is_available_for_rematch = models.BooleanField(
        null=True, blank=True, db_column="is_available_for_rematch"
    )
    is_editable = models.BooleanField(null=True, blank=True, db_column="is_editable")
    is_eoi = models.BooleanField(
        null=True, blank=True, db_column="is_eoi", verbose_name="Host"
    )
    is_person_of_interest = models.BooleanField(
        null=True, blank=True, db_column="is_person_of_interest"
    )
    is_principal = models.BooleanField(null=True, blank=True, db_column="is_principal")
    is_sponsor = models.BooleanField(
        null=True, blank=True, db_column="is_sponsor", verbose_name="Sponsor"
    )
    issue_date_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="issue_date_id",
        verbose_name="Issue date ID",
    )
    issuing_authority_of_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="issuing_authority_of_id",
        verbose_name="Issuing authority of ID",
    )
    last_name = models.TextField(null=True, blank=True, db_column="last_name")
    last_updated_date = models.DateTimeField(
        null=True, blank=True, db_column="last_updated_date"
    )
    national_identity_card_number = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="national_identity_card_number",
    )
    nationality = ArrayField(
        models.TextField(), null=True, blank=True, db_column="nationality"
    )
    notional_data = models.BooleanField(
        null=True, blank=True, db_column="notional_data"
    )
    organization_name = models.TextField(
        null=True, blank=True, db_column="organization_name"
    )
    organization_type = models.TextField(
        null=True, blank=True, db_column="organization_type"
    )
    other_nationalities = ArrayField(
        models.TextField(), null=True, blank=True, db_column="other_nationalities"
    )
    passport_details = ArrayField(
        models.TextField(), null=True, blank=True, db_column="passport_details"
    )
    phone_number = ArrayField(
        models.TextField(), null=True, blank=True, db_column="phone_number"
    )
    previous_id = models.TextField(
        null=True, blank=True, db_column="previous_id", verbose_name="Previous ID"
    )
    requested_checks_latest_date = models.DateTimeField(
        null=True, blank=True, db_column="requested_checks_latest_date"
    )
    residential_postcodes = ArrayField(
        models.TextField(), null=True, blank=True, db_column="residential_postcodes"
    )
    response_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="response_id",
        verbose_name="Response ID",
    )
    sex = models.TextField(null=True, blank=True, db_column="sex")
    source = ArrayField(models.TextField(), null=True, blank=True, db_column="source")
    sponsor_status = models.TextField(null=True, blank=True, db_column="sponsor_status")
    sponsor_type = models.TextField(
        choices=SponsorType.choices, null=True, blank=True, db_column="sponsor_type"
    )
    # Array of SponsorshipCertificationForm IDs
    sponsorship_certification_number_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="sponsorship_certification_number",
        verbose_name="Sponsorship certification application number",
    )
    survey_response = models.TextField(
        null=True, blank=True, db_column="survey_response"
    )
    application_unique_application_number = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="application_unique_application_number",
        verbose_name="Unique application number (UAN)",
    )
    unsubscribed = models.BooleanField(null=True, blank=True, db_column="unsubscribed")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
    edited_in_app = models.BooleanField(
        null=True, blank=True, db_column="edited_in_app"
    )

    def build_full_name(self):
        if self.first_name or self.last_name:
            return (f"{self.first_name or ''} {self.last_name or ''}").strip()
        return None

    def get_full_name(self):
        if self.full_name:
            return self.full_name
        return self.build_full_name()

    def display_link_data(self, linked_from, linked_as) -> LinkedRecordData:
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        display_name = self.get_full_name()
        if self.email:
            display_name = (
                f"{display_name} ({self.email})" if display_name else f"({self.email})"
            )

        if linked_as in ("Sponsor", "Sponsors") and isinstance(
            linked_from, MvAccommodationRequest
        ):
            sponsor_withdrawn = (
                self.id in linked_from.sponsor_withdrawn
                if linked_from.sponsor_withdrawn
                else False
            )

            return LinkedRecordData(
                "sponsors:detail-overview",
                self.id,
                display_name,
                "sponsor_withdrawn" if sponsor_withdrawn else None,
                "Withdrawn" if sponsor_withdrawn else None,
            )

        return LinkedRecordData(
            "sponsors:detail-overview",
            self.id,
            display_name,
        )

    def get_accommodation_requests(self):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        return MvAccommodationRequest.objects.filter(
            Q(active_host_id=self.id)
            | Q(primary_sponsor_id=self.id)
            | Q(sponsor_id__contains=[self.id])
        )

    def get_accommodation_requests_restrict_for_user(self, user: User):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        return MvAccommodationRequest.objects.get_for_user(user).filter(
            Q(active_host_id=self.id)
            | Q(primary_sponsor_id=self.id)
            | Q(sponsor_id__contains=[self.id])
        )

    def get_accommodations(self, user: User):
        from ontology.models.MvAccommodation import MvAccommodation

        return MvAccommodation.objects.filter(
            id__in=[a.id for a in self.accommodations.all()]
        )

    def get_accommodations_restrict_for_user(self, user: User):
        from ontology.models.MvAccommodation import MvAccommodation

        return MvAccommodation.objects.get_for_user(user).filter(
            id__in=[a.id for a in self.accommodations.all()]
        )

    def application_unique_application_number_restrict_for_user(self, user: User):
        from ontology.models.VisaApplication import VisaApplication

        if self.application_unique_application_number:
            return VisaApplication.objects.get_for_user(user).filter(
                application_unique_application_number__in=(
                    self.application_unique_application_number
                )
            )
        return VisaApplication.objects.none()

    def get_guests_restrict_for_user(self, user: User):
        guests = MvPerson.objects.none()

        accommodation_requests = self.get_accommodation_requests_restrict_for_user(user)
        for accommodation_request in accommodation_requests:
            guests |= accommodation_request.get_people_restrict_for_user(user)

        return guests

    def determine_dbs_check_status(self) -> DevCheckV2.CheckStatus:
        sponsor_checks = self.checks.filter(
            active=True, check_type__id=CheckType.Id.SPONSOR_DBS
        )
        if not sponsor_checks.exists():
            return DevCheckV2.CheckStatus.NOT_STARTED

        recorded_check_statuses = set(
            map(
                lambda status: validate_safeguarding_status(status),
                sponsor_checks.values_list("check_status", flat=True),
            )
        )

        prioritised_check_statuses = [
            DevCheckV2.CheckStatus.FAILED,
            DevCheckV2.CheckStatus.IN_PROGRESS,
            DevCheckV2.CheckStatus.NO_LONGER_NEEDED,
            DevCheckV2.CheckStatus.PASSED,
            DevCheckV2.CheckStatus.NOT_STARTED,
        ]
        for status in prioritised_check_statuses:
            if status in recorded_check_statuses:
                return status

        return DevCheckV2.CheckStatus.UNAVAILABLE

    def get_initials(self) -> str:
        initials = ""

        if self.first_name:
            initials += self.first_name[0]

        if self.last_name:
            initials += self.last_name[0]

        return initials.upper()

    def get_pii_safe_record_name(self) -> str:
        return self.get_initials()

    class Meta:
        verbose_name = "Host and Sponsor"

    def __str__(self):
        display_name = self.get_full_name()
        if not display_name:
            display_name = "[No name]"
        if self.email:
            display_name += " (" + self.email + ")"
        return display_name

    def save(self, *args, **kwargs):
        if not self.is_editable:
            raise ValidationError(
                "Error: Trying to save an MvVolunteer which is not editable"
            )

        self.full_name = self.build_full_name()
        self.edited_in_app = True
        super(MvVolunteer, self).save(*args, **kwargs)
