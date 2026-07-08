from datetime import date, datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Case, Q, QuerySet, Value, When
from django.db.models.functions import Concat

from accounts.models import User
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models import DevCheckV2
from ontology.utils import LinkedRecordData


class MvPersonQuerySet(models.QuerySet):
    def with_full_name(self):
        missing_first_name = Q(first_name__isnull=True) | Q(first_name__exact="")
        missing_last_name = Q(last_name__isnull=True) | Q(last_name__exact="")

        return self.annotate(
            full_name=Case(
                When(
                    missing_first_name & missing_last_name,
                    then=Value(None, output_field=models.TextField()),
                ),
                default=Concat(
                    "first_name",
                    Value(" "),
                    "last_name",
                    output_field=models.TextField(),
                ),
                output_field=models.TextField(),
            )
        )


class MvPersonManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def get_queryset(self):
        return MvPersonQuerySet(self.model, using=self._db).with_full_name()

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(accommodation_request__ltla_name__overlap=ltla_names) & ~Q(
            accommodation_request__ltla_name__contained_by=[]
        )

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(accommodation_request__utla_name__overlap=utla_names) & ~Q(
            accommodation_request__utla_name__contained_by=[]
        )

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class MvPerson(models.Model):
    class UPEVisaStatus(models.TextChoices):
        NO_OUTCOME = "NO_OUTCOME", "No UPE visa application outcome"
        ACCEPTED = "UPE_VISA_ACCEPTED", "UPE visa accepted"
        REFUSED = "UPE_VISA_REFUSED", "UPE visa refused"
        REJECTED = "UPE_VISA_REJECTED", "UPE visa rejected"
        WITHDRAWN = "UPE_VISA_WITHDRAWN", "UPE visa withdrawn"

    objects = MvPersonManager()
    checks: QuerySet[DevCheckV2]

    accommodation_request = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_constraint=False,
        db_column="accommodation_request_id",
        verbose_name="Accommodation request ID",
    )
    adverse_rematch = models.BooleanField(
        null=True, blank=True, db_column="adverse_rematch"
    )
    age = models.BigIntegerField(null=True, blank=True, db_column="age")
    application_number = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="application_number",
        verbose_name="Unique application number (UAN)",
    )
    can_be_contacted_by_phone = models.TextField(
        null=True, blank=True, db_column="can_be_contacted_by_phone"
    )
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    created_by = models.TextField(null=True, blank=True, db_column="created_by")
    date_of_birth = models.DateField(null=True, blank=True, db_column="date_of_birth")
    date_of_first_issue_visa_decision = models.DateField(
        null=True,
        blank=True,
        db_column="date_of_first_issue_visa_decision",
        verbose_name="Earliest issued visa decision date",
    )
    disability_flag = models.BooleanField(
        null=True, blank=True, db_column="disability_flag"
    )
    is_uam = models.BooleanField(
        null=True, blank=True, db_column="is_uam", verbose_name="Eligible minor"
    )
    email = ArrayField(models.TextField(), null=True, blank=True, db_column="email")
    email_after_decision = ArrayField(
        models.TextField(), null=True, blank=True, db_column="email_after_decision"
    )
    email_for_decision = ArrayField(
        models.TextField(), null=True, blank=True, db_column="email_for_decision"
    )
    email_for_questions = ArrayField(
        models.TextField(), null=True, blank=True, db_column="email_for_questions"
    )
    arrival_date = models.DateField(
        null=True,
        blank=True,
        db_column="arrival_date",
        verbose_name="First arrival date",
    )
    arrival_port_code = models.TextField(
        null=True,
        blank=True,
        db_column="arrival_port_code",
        verbose_name="First arrival port code",
    )
    arrival_port_name = models.TextField(
        null=True,
        blank=True,
        db_column="arrival_port_name",
        verbose_name="First arrival port name",
    )
    first_name = models.TextField(null=True, blank=True, db_column="first_name")
    group = models.ForeignKey(
        "ontology.MvGroup",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="group_id",
        verbose_name="Group ID",
    )
    gwf = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="gwf",
        verbose_name="Global web form number (GWF)",
    )
    id = models.TextField(primary_key=True, db_column="id", verbose_name="ID")
    is_principal = models.BooleanField(null=True, blank=True, db_column="is_principal")
    is_uam_edited_time = models.DateTimeField(
        null=True, blank=True, db_column="is_uam_edited_time"
    )
    last_edited_at = models.DateTimeField(
        null=True, blank=True, db_column="last_edited_at"
    )
    last_edited_by = models.TextField(null=True, blank=True, db_column="last_edited_by")
    last_name = models.TextField(null=True, blank=True, db_column="last_name")
    latest_arrival_date = models.DateField(
        null=True, blank=True, db_column="latest_arrival_date"
    )
    visa_application_date_maximum = models.DateField(
        null=True,
        blank=True,
        db_column="visa_application_date_maximum",
        verbose_name="Latest visa application date",
    )
    nationality = ArrayField(
        models.TextField(), null=True, blank=True, db_column="nationality"
    )
    notional_data = models.BooleanField(
        null=True, blank=True, db_column="notional_data"
    )
    old_group = models.ForeignKey(
        "ontology.MvGroup",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="old_group_id",
        db_constraint=False,
        verbose_name="Old group ID",
    )
    passport_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="passport_id",
        verbose_name="Passport number",
    )
    phone = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="phone",
        verbose_name="Phone number",
    )
    # Array of previous group IDs
    previous_group_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="previous_group_ids",
        verbose_name="Previous group ID",
    )
    # Actual ManyToManyField for previous group IDs
    previous_group_ids = models.ManyToManyField(
        "ontology.MvGroup",
        related_name="+",
        blank=True,
        db_column="previous_group_ids",
        verbose_name="Previous group IDs",
    )
    previous_group_leaving_times = ArrayField(
        models.DateTimeField(),
        null=True,
        blank=True,
        db_column="previous_group_leaving_times",
    )
    primary_application_numbers = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="primary_application_numbers",
    )
    gender = models.TextField(
        null=True, blank=True, db_column="gender", verbose_name="Sex"
    )
    source = ArrayField(models.TextField(), null=True, blank=True, db_column="source")
    # Array of SponsorshipCertificationForm IDs
    sponsorship_certification_number_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="sponsorship_certification_number",
        verbose_name="Sponsorship certification application number",
    )
    title = models.TextField(null=True, blank=True, db_column="title")
    travelling_to_uk = models.BooleanField(
        null=True,
        blank=True,
        db_column="travelling_to_uk",
        verbose_name="Travelling to UK",
    )
    upe_visa_status = models.TextField(
        null=True,
        blank=True,
        db_column="upe_visa_status",
        verbose_name="UPE visa status",
        choices=UPEVisaStatus.choices,
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
    visa_application_date = models.DateField(
        null=True, blank=True, db_column="visa_application_date"
    )
    visa_application_dates = ArrayField(
        models.DateField(), null=True, blank=True, db_column="visa_application_dates"
    )
    visa_decision_date = models.DateField(
        null=True, blank=True, db_column="visa_decision_date"
    )
    visa_status = models.TextField(
        null=True,
        blank=True,
        db_column="visa_status",
        verbose_name="Latest visa status",
    )
    wheelchair_required = models.BooleanField(
        null=True, blank=True, db_column="wheelchair_required"
    )
    edited_in_app = models.BooleanField(
        null=True, blank=True, db_column="edited_in_app"
    )
    archived_at = models.DateTimeField(null=True, blank=True, db_column="archived_at")
    is_archived = models.BooleanField(
        null=False, default=False, db_column="is_archived"
    )

    class Meta:
        verbose_name = "Guest"

    def display_link_data(self, linked_from, linked_as) -> LinkedRecordData:
        display_name = self.get_full_name()
        if self.email:
            email_suffix = f"({self.email[0]})"
            if display_name:
                display_name += " " + email_suffix
            else:
                display_name = email_suffix

        return LinkedRecordData("guests:detail-overview", self.id, display_name)

    def get_or_estimate_date_of_birth(self) -> date:
        """Estimates a person's date of birth"""

        if self.date_of_birth:
            return self.date_of_birth

        today = datetime.now().date()
        if self.age:
            return date(today.year - self.age, today.month, 1)

        return today

    def get_full_name(self):
        if self.first_name or self.last_name:
            return (f"{self.first_name or ''} {self.last_name or ''}").strip()
        return None

    def get_initials(self) -> str:
        initials = ""

        if self.first_name:
            initials += self.first_name[0]

        if self.last_name:
            initials += self.last_name[0]

        return initials.upper()

    def get_pii_safe_record_name(self) -> str:
        return self.get_initials()

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return full_name
        return super().__str__()

    def save(self, *args, **kwargs):
        self.edited_in_app = True
        super(MvPerson, self).save(*args, **kwargs)

    def update_primary_contact_on_linked_objects(self):
        if self.group.is_primary_contact(self):
            self.group.refresh_data()
        if self.accommodation_request.is_primary_contact(self):
            self.accommodation_request.update_primary_contact(self)

    def get_page_title(self) -> str:
        name = self.get_full_name() or "Unknown"
        address_part = None
        accommodation_request = self.get_accommodation_request()
        if accommodation_request and accommodation_request.get_primary_accommodation():
            accommodation = accommodation_request.get_primary_accommodation()
            full_address = getattr(accommodation, "full_address", None)
            postcode_obj = getattr(accommodation, "postcode", None)
            postcode = (
                getattr(postcode_obj, "postcode_formatted", None)
                if postcode_obj
                else None
            )
            if full_address:
                address_part = full_address[:14]
                if postcode:
                    address_part += f", {postcode}"
        if address_part:
            return f"{name} to {address_part}"
        return name

    def get_visa_applications_restrict_for_user(self, user: User):
        from ontology.models.VisaApplication import VisaApplication

        if not self.application_number:
            return VisaApplication.objects.none()

        return VisaApplication.objects.get_for_user(user).filter(
            application_unique_application_number__in=self.application_number
        )

    def get_visa_applications(self, user: User = None):
        from ontology.models.VisaApplication import VisaApplication

        if not self.application_number:
            return VisaApplication.objects.none()

        if user:
            visa_applications = (
                VisaApplication.objects.get_all_annotate_with_user_can_view(user)
            )
        else:
            visa_applications = VisaApplication.objects.all()

        return visa_applications.filter(
            application_unique_application_number__in=self.application_number
        )

    def get_accommodation_request(self):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        if self.accommodation_request_id:
            return MvAccommodationRequest.objects.filter(
                id=self.accommodation_request_id
            ).first()

        return None

    def accommodation_request_restrict_for_user(self, user: User):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        if self.accommodation_request_id:
            return (
                MvAccommodationRequest.objects.get_for_user(user)
                .filter(id=self.accommodation_request_id)
                .first()
            )
        return None


def get_person_age_sort_key(person: MvPerson):
    if not person:
        return None

    return person.get_or_estimate_date_of_birth(), person.id
