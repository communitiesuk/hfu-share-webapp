from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Case, Q, Value, When
from django.db.models.functions import Concat

from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.utils import LinkedRecordData


class SponsorshipCertificationFormQuerySet(models.QuerySet):
    def with_sponsor_full_name(self):
        missing_given_name = Q(given_name__isnull=True) | Q(given_name__exact="")
        missing_family_name = Q(family_name__isnull=True) | Q(family_name__exact="")

        return self.annotate(
            sponsor_full_name=Case(
                When(
                    missing_given_name & missing_family_name,
                    then=Value(None, output_field=models.TextField()),
                ),
                default=Concat(
                    "given_name",
                    Value(" "),
                    "family_name",
                    output_field=models.TextField(),
                ),
                output_field=models.TextField(),
            )
        )


class SponsorshipCertificationFormManager(
    LocalAuthorityPermissionsManagerMixin, models.Manager
):
    def get_queryset(self):
        return SponsorshipCertificationFormQuerySet(
            self.model, using=self._db
        ).with_sponsor_full_name()

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(ltla_name__overlap=ltla_names) & ~Q(ltla_name__contained_by=[])

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(utla_name__overlap=utla_names) & ~Q(utla_name__contained_by=[])

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class SponsorshipCertificationForm(models.Model):
    objects = SponsorshipCertificationFormManager()

    class IdentificationType(models.TextChoices):
        PASSPORT = ("passport", "Passport")
        NATIONAL_IDENTITY_CARD = ("national_identity_card", "National Identity Card")
        BIOMETRIC_RESIDENCE = (
            "biometric_residence",
            "Biometric Residence Permit or Card",
        )
        PHOTO_DRIVING_LICENCE = ("photo_driving_licence", "Photo driving licence")
        REFUGEE_TRAVEL_DOCUMENT = ("refugee_travel_document", "Refugee Travel Document")
        NONE = ("none", "None provided")

    certificate_reference = models.TextField(
        null=True,
        blank=True,
        db_column="certificate_reference",
        verbose_name="Child sponsorship approval number",
    )
    cohabitant_date_of_birth = ArrayField(
        models.TextField(), null=True, blank=True, db_column="cohabitant_date_of_birth"
    )
    cohabitant_family_name = ArrayField(
        models.TextField(), null=True, blank=True, db_column="cohabitant_family_name"
    )
    cohabitant_given_name = ArrayField(
        models.TextField(), null=True, blank=True, db_column="cohabitant_given_name"
    )
    cohabitant_id = ArrayField(
        models.TextField(), null=True, blank=True, db_column="cohabitant_id"
    )
    cohabitant_id_type_and_number = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="cohabitant_id_type_and_number",
    )
    cohabitant_nationality = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="cohabitant_nationality",
        verbose_name="Nationality",
    )
    created_at = models.DateTimeField(
        null=True, blank=True, db_column="created_at", verbose_name="Date created"
    )
    different_address = models.BooleanField(
        null=True, blank=True, db_column="different_address"
    )
    email = models.TextField(
        null=True, blank=True, db_column="email", verbose_name="Email address"
    )
    family_name = models.TextField(
        null=True, blank=True, db_column="family_name", verbose_name="Last name"
    )
    ingestion_time = models.DateTimeField(null=True, blank=True)
    given_name = models.TextField(
        null=True, blank=True, db_column="given_name", verbose_name="First name"
    )
    has_other_names = models.BooleanField(
        null=True, blank=True, db_column="has_other_names"
    )
    has_other_nationalities = models.BooleanField(
        null=True, blank=True, db_column="has_other_nationalities"
    )
    has_parental_consent = models.BooleanField(
        null=True, blank=True, db_column="has_parental_consent"
    )
    identification_number = models.TextField(
        null=True,
        blank=True,
        db_column="identification_number",
        verbose_name="Identification number",
    )
    identification_type = models.TextField(
        null=True,
        blank=True,
        db_column="identification_type",
        verbose_name="Identification type",
        choices=IdentificationType.choices,
    )
    is_committed = models.BooleanField(null=True, blank=True, db_column="is_committed")
    is_consent = models.BooleanField(null=True, blank=True, db_column="is_consent")
    is_living_december = models.BooleanField(
        null=True, blank=True, db_column="is_living_december"
    )
    is_permitted = models.BooleanField(null=True, blank=True, db_column="is_permitted")
    is_unaccompanied = models.BooleanField(
        null=True, blank=True, db_column="is_unaccompanied"
    )
    is_under_18 = models.BooleanField(null=True, blank=True, db_column="is_under_18")
    ltla_name = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="ltla_name",
        verbose_name="Local authority",
    )
    minor_contact_type = models.TextField(
        null=True, blank=True, db_column="minor_contact_type"
    )
    minor_date_of_birth = models.DateField(
        null=True, blank=True, db_column="minor_date_of_birth"
    )
    minor_email = models.TextField(null=True, blank=True, db_column="minor_email")
    minor_family_name = models.TextField(
        null=True, blank=True, db_column="minor_family_name"
    )
    minor_given_name = models.TextField(
        null=True, blank=True, db_column="minor_given_name"
    )
    minor_phone_number = models.TextField(
        null=True, blank=True, db_column="minor_phone_number"
    )
    nationality = ArrayField(
        models.TextField(), null=True, blank=True, db_column="nationality"
    )
    notification_sent = models.BooleanField(
        null=True, blank=True, db_column="notification_sent"
    )
    notification_timestamp = models.DateTimeField(
        null=True, blank=True, db_column="notification_timestamp"
    )
    notional_data = models.BooleanField(
        null=True, blank=True, db_column="notional_data"
    )
    other_adults_address = models.BooleanField(
        null=True, blank=True, db_column="other_adults_address"
    )
    other_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="other_names"
    )
    phone_number = models.TextField(
        null=True, blank=True, db_column="phone_number", verbose_name="Phone number"
    )
    residential_line_1 = models.TextField(
        null=True, blank=True, db_column="residential_line_1"
    )
    residential_line_2 = models.TextField(
        null=True, blank=True, db_column="residential_line_2"
    )
    residential_postcode = models.TextField(
        null=True, blank=True, db_column="residential_postcode", verbose_name="Postcode"
    )
    residential_town = models.TextField(
        null=True, blank=True, db_column="residential_town"
    )
    sponsor_date_of_birth = models.DateField(
        null=True,
        blank=True,
        db_column="sponsor_date_of_birth",
        verbose_name="Date of birth",
    )
    sponsor_declaration = models.TextField(
        null=True, blank=True, db_column="sponsor_declaration"
    )
    reference = models.TextField(
        primary_key=True, db_column="reference", verbose_name="Application Number"
    )
    started_at = models.DateTimeField(null=True, blank=True, db_column="started_at")
    uk_parental_consent_file_size = models.BigIntegerField(
        null=True, blank=True, db_column="uk_parental_consent_file_size"
    )
    uk_parental_consent_file_type = models.TextField(
        null=True, blank=True, db_column="uk_parental_consent_file_type"
    )
    uk_parental_consent_filename = models.TextField(
        null=True, blank=True, db_column="uk_parental_consent_filename"
    )
    uk_parental_consent_saved_filename = models.TextField(
        null=True, blank=True, db_column="uk_parental_consent_saved_filename"
    )
    ukraine_parental_consent_file_size = models.BigIntegerField(
        null=True, blank=True, db_column="ukraine_parental_consent_file_size"
    )
    ukraine_parental_consent_file_type = models.TextField(
        null=True, blank=True, db_column="ukraine_parental_consent_file_type"
    )
    ukraine_parental_consent_filename = models.TextField(
        null=True, blank=True, db_column="ukraine_parental_consent_filename"
    )
    ukraine_parental_consent_saved_filename = models.TextField(
        null=True, blank=True, db_column="ukraine_parental_consent_saved_filename"
    )
    utla_name = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="utla_name",
        verbose_name="Upper tier LA",
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )

    def get_accommodation_requests_restrict_for_user(self, user):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        return (
            MvAccommodationRequest.objects.get_for_user(user)
            .filter(sponsorship_certification_number_id__overlap=[self.reference])
            .all()
        )

    def get_person_restrict_for_user(self, user):
        from ontology.models.MvPerson import MvPerson

        return (
            MvPerson.objects.get_for_user(user)
            .filter(sponsorship_certification_number_id__overlap=[self.reference])
            .first()
        )

    def get_initials(self) -> str:
        initials = ""

        if self.given_name:
            initials += self.given_name[0]

        if self.family_name:
            initials += self.family_name[0]

        return initials.upper()

    def get_pii_safe_record_name(self) -> str:
        return self.get_initials()

    class Meta:
        verbose_name = "Uam"

    def display_link_data(self, linked_from, linked_as) -> LinkedRecordData:
        return LinkedRecordData(
            "uams:detail-overview",
            self.pk,
            f"{self.given_name} {self.family_name}",
        )

    def __str__(self):
        return f"{self.given_name} {self.family_name}" or super().__str__()
