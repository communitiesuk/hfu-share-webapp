from enum import Enum

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import Case, Q, Value, When
from django.db.models.functions import Concat

from accounts.models import User
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models.MvInteraction import MvInteraction
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

    class PreApprovalCheckStatus(models.TextChoices):
        NOT_STARTED = ("Not started", "Not started")
        IN_PROGRESS = ("In progress", "In progress")
        PASSED = ("Passed", "Passed")
        FAILED = ("Failed", "Failed")

    class PreApprovalStatus(models.TextChoices):
        """
        Overall status of the pre-approval checks, worked out from the
        individual check fields. Used for display only, not stored.
        """

        WAITING_FOR_UKVI_CHECKS = ("Waiting for UKVI checks", "Waiting for UKVI checks")
        UKVI_CHECKS_IN_PROGRESS = ("UKVI checks in progress", "UKVI checks in progress")
        FAILED_UKVI_CHECKS = ("Failed UKVI checks", "Failed UKVI checks")
        WAITING_FOR_LA_CHECKS = ("Waiting for LA checks", "Waiting for LA checks")
        LA_CHECKS_IN_PROGRESS = ("LA checks in progress", "LA checks in progress")
        FAILED_LA_CHECKS = ("Failed LA checks", "Failed LA checks")
        PASSED_ALL_CHECKS = ("Passed all checks", "Passed all checks")
        COMPLETED = ("Completed", "Completed")
        # Applications submitted before the pre-approval process was added
        STATUS_NOT_RECORDED = ("Status not recorded", "Status not recorded")

    class PreApprovalCheckCodeSentStatus(Enum):
        CANNOT_SEND_CODE = "Cannot send code"
        NO_LONGER_NEEDED = "No longer needed"
        CODE_NOT_SENT = "Code not sent"
        CODE_SENT = "Code sent"

    UKVI_CHECK_FIELDS = (
        "uk_consent_form_status",
        "ukraine_consent_form_status",
        "sponsor_immigration_eligibility_status",
        "sponsor_household_security_checks_status",
    )
    LA_CHECK_FIELDS = (
        "sponsor_household_enhanced_dbs_status",
        "accommodation_exists_status",
        "accommodation_suitable_status",
        "sponsor_role_and_expectations_status",
        "sponsor_arrangements_suitable_status",
    )

    PRE_APPROVAL_CHECK_INTERACTION = {
        "uk_consent_form_status": {
            "title": MvInteraction.InteractionContact.UK_CONSENT_FORM_STATUS_CHECK,
            "note": "UK consent form: {check_status}",
        },
        "ukraine_consent_form_status": {
            "title": MvInteraction.InteractionContact.UKRAINE_CONSENT_FORM_STATUS_CHECK,
            "note": "Ukraine consent form: {check_status}",
        },
        "sponsor_immigration_eligibility_status": {
            "title": (
                MvInteraction.InteractionContact.SPONSOR_IMMIGRATION_ELIGIBILITY_STATUS_CHECK
            ),
            "note": "Sponsor immigration eligibility: {check_status}",
        },
        "sponsor_household_security_checks_status": {
            "title": (
                MvInteraction.InteractionContact.SPONSOR_HOUSEHOLD_SECURITY_CHECKS_STATUS_CHECK
            ),
            "note": "Sponsor and household security checks: {check_status}",
        },
        "sponsor_household_enhanced_dbs_status": {
            "title": (
                MvInteraction.InteractionContact.SPONSOR_HOUSEHOLD_ENHANCED_DBS_STATUS_CHECK
            ),
            "note": "Sponsor and household members enhanced DBS: {check_status}",
        },
        "accommodation_exists_status": {
            "title": (MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK),
            "note": "Accommodation exists: {check_status}",
        },
        "accommodation_suitable_status": {
            "title": (
                MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_STATUS_CHECK
            ),
            "note": "Accommodation suitable: {check_status}",
        },
        "sponsor_role_and_expectations_status": {
            "title": (
                MvInteraction.InteractionContact.SPONSOR_ROLE_AND_EXPECTATIONS_STATUS_CHECK
            ),
            "note": "Sponsor role and expectations: {check_status}",
        },
        "sponsor_arrangements_suitable_status": {
            "title": (
                MvInteraction.InteractionContact.SPONSOR_ARRANGEMENTS_SUITABLE_STATUS_CHECK
            ),
            "note": "Sponsor arrangements suitable: {check_status}",
        },
        "sponsor_certification_code_emailed": {
            "title": (
                MvInteraction.InteractionContact.SPONSOR_CERTIFICATION_CODE_EMAILED_CHECK
            ),
            "note": ("Sponsor certification code: {reference_code} emailed to sponsor"),
        },
    }

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
        primary_key=True, db_column="reference", verbose_name="Application number"
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
    # UKVI checks
    uk_consent_form_status = models.TextField(
        null=True,
        blank=True,
        db_column="uk_consent_form_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="UK consent form",
    )
    ukraine_consent_form_status = models.TextField(
        null=True,
        blank=True,
        db_column="ukraine_consent_form_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Ukraine consent form",
    )
    sponsor_immigration_eligibility_status = models.TextField(
        null=True,
        blank=True,
        db_column="sponsor_immigration_eligibility_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Sponsor immigration eligibility",
    )
    sponsor_household_security_checks_status = models.TextField(
        null=True,
        blank=True,
        db_column="sponsor_household_security_checks_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Sponsor and household security checks",
    )
    # Local authority checks
    sponsor_household_enhanced_dbs_status = models.TextField(
        null=True,
        blank=True,
        db_column="sponsor_household_enhanced_dbs_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Sponsor and household members enhanced DBS",
    )
    accommodation_exists_status = models.TextField(
        null=True,
        blank=True,
        db_column="accommodation_exists_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Accommodation exists",
    )
    accommodation_suitable_status = models.TextField(
        null=True,
        blank=True,
        db_column="accommodation_suitable_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Accommodation suitable",
    )
    sponsor_role_and_expectations_status = models.TextField(
        null=True,
        blank=True,
        db_column="sponsor_role_and_expectations_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Sponsor role and expectations",
    )
    sponsor_arrangements_suitable_status = models.TextField(
        null=True,
        blank=True,
        db_column="sponsor_arrangements_suitable_status",
        choices=PreApprovalCheckStatus.choices,
        verbose_name="Sponsor arrangements suitable",
    )
    sponsor_certification_code_emailed = models.BooleanField(
        db_column="sponsor_certification_code_emailed",
        db_default=False,
        verbose_name="Code sent to sponsor",
    )

    def _summarise_checks(self, check_fields: tuple[str, ...]) -> tuple[int, bool]:
        statuses = [getattr(self, field) for field in check_fields]
        recorded = [
            status
            for status in statuses
            if status
            in (
                self.PreApprovalCheckStatus.IN_PROGRESS,
                self.PreApprovalCheckStatus.PASSED,
                self.PreApprovalCheckStatus.FAILED,
            )
        ]
        return (
            len(recorded),
            self.PreApprovalCheckStatus.IN_PROGRESS in recorded,
            self.PreApprovalCheckStatus.FAILED in recorded,
        )

    def get_pre_approval_status(self) -> PreApprovalStatus:
        """
        The UKVI checks are done first, then the LA checks, then the sponsor
        certification code is emailed to the sponsor. A set of checks fails as
        soon as any check in it fails, and only passes once every check in it
        has passed.
        """
        all_check_fields = self.UKVI_CHECK_FIELDS + self.LA_CHECK_FIELDS
        if all(getattr(self, field) is None for field in all_check_fields):
            return self.PreApprovalStatus.STATUS_NOT_RECORDED

        ukvi_recorded, ukvi_in_progress, ukvi_failed = self._summarise_checks(
            self.UKVI_CHECK_FIELDS
        )
        if ukvi_failed:
            return self.PreApprovalStatus.FAILED_UKVI_CHECKS
        if ukvi_recorded == 0:
            return self.PreApprovalStatus.WAITING_FOR_UKVI_CHECKS
        if ukvi_in_progress or ukvi_recorded < len(self.UKVI_CHECK_FIELDS):
            return self.PreApprovalStatus.UKVI_CHECKS_IN_PROGRESS

        la_recorded, la_in_progress, la_failed = self._summarise_checks(
            self.LA_CHECK_FIELDS
        )
        if la_failed:
            return self.PreApprovalStatus.FAILED_LA_CHECKS
        if la_recorded == 0:
            return self.PreApprovalStatus.WAITING_FOR_LA_CHECKS
        if la_in_progress or la_recorded < len(self.LA_CHECK_FIELDS):
            return self.PreApprovalStatus.LA_CHECKS_IN_PROGRESS

        if not self.sponsor_certification_code_emailed:
            return self.PreApprovalStatus.PASSED_ALL_CHECKS

        return self.PreApprovalStatus.COMPLETED

    def get_pre_approval_check_code_sent_status(self) -> PreApprovalCheckCodeSentStatus:
        pre_approval_status = self.get_pre_approval_status()
        if pre_approval_status in [
            self.PreApprovalStatus.PASSED_ALL_CHECKS,
            self.PreApprovalStatus.COMPLETED,
        ]:
            if self.sponsor_certification_code_emailed:
                return self.PreApprovalCheckCodeSentStatus.CODE_SENT

            return self.PreApprovalCheckCodeSentStatus.CODE_NOT_SENT

        if pre_approval_status is self.PreApprovalStatus.FAILED_UKVI_CHECKS:
            return self.PreApprovalCheckCodeSentStatus.NO_LONGER_NEEDED

        return self.PreApprovalCheckCodeSentStatus.CANNOT_SEND_CODE

    @transaction.atomic
    def update_pre_approval_check_status(
        self, attribute: str, check: PreApprovalCheckStatus | bool, user: User
    ):
        if (
            attribute not in self.UKVI_CHECK_FIELDS
            and attribute not in self.LA_CHECK_FIELDS
            and attribute != "sponsor_certification_code_emailed"
        ):
            raise ValueError(f"Unknown pre-approval check attribute: {attribute!r}")

        setattr(self, attribute, check)
        self.save(update_fields=[attribute])

        interaction_details = self.PRE_APPROVAL_CHECK_INTERACTION[attribute]
        interaction_title = interaction_details["title"]

        if attribute == "sponsor_certification_code_emailed":
            format_kwargs = {"reference_code": self.certificate_reference}
        else:
            format_kwargs = {"check_status": check.lower()}

        interaction_notes = interaction_details["note"].format(**format_kwargs)

        MvInteraction.objects.create(
            interaction_contact=interaction_title,
            interaction_type=interaction_title,
            linked_uam=self,
            interaction_notes=interaction_notes,
            created_by=user,
            title=interaction_title,
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

    def get_full_name(self):
        name = f"{self.given_name or ''} {self.family_name or ''}".strip()
        return name or "Unknown"

    def display_link_data(self, linked_from, linked_as) -> LinkedRecordData:
        return LinkedRecordData(
            "uams:detail-overview",
            self.pk,
            self.get_full_name(),
        )

    def __str__(self):
        return self.get_full_name()
