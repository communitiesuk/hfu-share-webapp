from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from accounts.enums import GroupType
from accounts.models import GroupInfo, User
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models.MvUkPostcode import MvUkPostcode
from ontology.models.MvVolunteer import MvVolunteer
from ontology.models.VisaApplication import VisaApplication
from ontology.utils import LinkedRecordData


class MvAccommodationManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("postcode")

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(ltla_name__in=ltla_names)

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(utla_name__in=utla_names)

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class MvAccommodation(models.Model):
    objects = MvAccommodationManager()

    class AccommodationType(models.TextChoices):
        SPONSOR_ACCOMMODATION = ("Sponsor Accommodation",)
        TEMPORARY_ACCOMMODATION = ("Temporary Accommodation",)

    accommodation_availability = models.TextField(
        null=True, blank=True, db_column="accommodation_availability"
    )
    accommodation_provider = models.TextField(
        null=True, blank=True, db_column="accommodation_provider"
    )
    accommodation_provider_type = models.TextField(
        null=True, blank=True, db_column="accommodation_provider_type"
    )
    accommodation_type = models.TextField(
        choices=AccommodationType.choices,
        null=True,
        blank=True,
        db_column="accommodation_type",
    )
    airbnb_avg_rating = models.FloatField(
        null=True,
        blank=True,
        db_column="airbnb_avg_rating",
        verbose_name="Airbnb average rating",
    )
    airbnb_num_ratings = models.IntegerField(
        null=True,
        blank=True,
        db_column="airbnb_num_ratings",
        verbose_name="Airbnb number of ratings",
    )
    airbnb_super_host = models.BooleanField(
        null=True,
        blank=True,
        db_column="airbnb_super_host",
        verbose_name="Airbnb Superhost",
    )
    allow_pet = models.BooleanField(null=True, blank=True, db_column="allow_pet")
    application_unique_application_number = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="application_unique_application_number",
        verbose_name="Unique application number (UAN)",
    )
    availability_end_date = models.DateField(
        null=True, blank=True, db_column="availability_end_date"
    )
    availability_start_date = models.DateField(
        null=True, blank=True, db_column="availability_start_date"
    )
    building_name = models.TextField(null=True, blank=True, db_column="building_name")
    building_number = models.TextField(
        null=True, blank=True, db_column="building_number"
    )
    can_be_considered_for_accommodation = models.BooleanField(
        null=True, blank=True, db_column="can_be_considered_for_accommodation"
    )
    comments = models.TextField(null=True, blank=True, db_column="comments")
    country = models.TextField(null=True, blank=True, db_column="country")
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    created_by = models.TextField(null=True, blank=True, db_column="created_by")
    created_date = models.DateTimeField(null=True, blank=True, db_column="created_date")
    current_capacity = models.IntegerField(
        null=True, blank=True, db_column="current_capacity"
    )
    deliminated_address = ArrayField(
        models.TextField(null=True, blank=True),
        null=True,
        blank=True,
        db_column="deliminated_address",
    )
    family_friendly = models.BooleanField(
        null=True, blank=True, db_column="family_friendly"
    )
    full_address = models.TextField(
        null=True, blank=True, db_column="full_address", verbose_name="Address"
    )
    geohash = models.TextField(null=True, blank=True, db_column="geohash")
    google_hotel_num_ratings = models.IntegerField(
        null=True,
        blank=True,
        db_column="google_hotel_num_ratings",
        verbose_name="Google hotel number of ratings",
    )
    google_hotel_rating = models.FloatField(
        null=True, blank=True, db_column="google_hotel_rating"
    )
    streetview_link = models.TextField(
        null=True, blank=True, db_column="streetview_link"
    )
    gwf = ArrayField(
        models.TextField(), null=True, blank=True, db_column="gwf", verbose_name="GWF"
    )
    handrails_leading_to_main_entrance = models.BooleanField(
        null=True, blank=True, db_column="handrails_leading_to_main_entrance"
    )
    host_id_DEPRECATED = models.TextField(
        null=True, blank=True, db_column="host_id", verbose_name="Host ID"
    )
    id = models.TextField(primary_key=True, db_column="id", verbose_name="ID")
    inspection_date = models.DateField(
        null=True, blank=True, db_column="inspection_date"
    )
    is_accommodation = models.BooleanField(
        null=True, blank=True, db_column="is_accommodation"
    )
    is_available_for_rematch = models.BooleanField(
        null=True, blank=True, db_column="is_available_for_rematch"
    )
    is_editable = models.BooleanField(null=True, blank=True, db_column="is_editable")
    is_eoi = models.BooleanField(
        null=True, blank=True, db_column="is_eoi", verbose_name="Is EOI"
    )
    is_principal = models.BooleanField(null=True, blank=True, db_column="is_principal")
    is_residential = models.BooleanField(
        null=True, blank=True, db_column="is_residential"
    )
    last_modified_date = models.DateTimeField(
        null=True, blank=True, db_column="last_modified_date"
    )
    listed_capacity = models.IntegerField(
        null=True, blank=True, db_column="listed_capacity"
    )
    local_authority = models.TextField(
        null=True, blank=True, db_column="local_authority"
    )
    ltla_name = models.TextField(
        null=True, blank=True, db_column="ltla_name", verbose_name="Lower tier LA"
    )
    notional_data = models.BooleanField(
        null=True, blank=True, db_column="notional_data"
    )
    number_adults = models.BigIntegerField(
        null=True, blank=True, db_column="number_adults"
    )
    number_children = models.BigIntegerField(
        null=True, blank=True, db_column="number_children"
    )
    number_of_double_rooms_available = models.BigIntegerField(
        null=True, blank=True, db_column="number_of_double_rooms_available"
    )
    number_of_single_rooms = models.BigIntegerField(
        null=True, blank=True, db_column="number_of_single_rooms"
    )
    pest_infestation = models.BooleanField(
        null=True, blank=True, db_column="pest_infestation"
    )
    postcode = models.ForeignKey(
        "ontology.MvUkPostcode",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_constraint=False,
        db_column="postcode",
    )
    reference = ArrayField(
        models.TextField(), null=True, blank=True, db_column="reference"
    )
    requested_checks_latest_date = models.DateTimeField(
        null=True, blank=True, db_column="requested_checks_latest_date"
    )
    response_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="response_id",
        verbose_name="Response ID",
    )
    roof_in_good_shape = models.BooleanField(
        null=True, blank=True, db_column="roof_in_good_shape"
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
    step_free_access = models.BooleanField(
        null=True, blank=True, db_column="step_free_access"
    )
    street_name_1 = models.TextField(null=True, blank=True, db_column="street_name_1")
    street_name_2 = models.TextField(null=True, blank=True, db_column="street_name_2")
    submission_guid = models.TextField(
        null=True,
        blank=True,
        db_column="submission_guid",
        verbose_name="Submission GUID",
    )
    submission_guids = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="submission_guids",
        verbose_name="Submission GUIDs",
    )
    submitted_date = models.DateTimeField(
        null=True, blank=True, db_column="submitted_date"
    )
    sufficient_smoke_alarms = models.BooleanField(
        null=True, blank=True, db_column="sufficient_smoke_alarms"
    )
    town_city = models.TextField(null=True, blank=True, db_column="town_city")
    unsubscribed = models.BooleanField(null=True, blank=True, db_column="unsubscribed")
    unsuitable = models.BooleanField(null=True, blank=True, db_column="unsuitable")
    up_to_code = models.BooleanField(null=True, blank=True, db_column="up_to_code")
    utla_name = models.TextField(
        null=True, blank=True, db_column="utla_name", verbose_name="Upper tier LA"
    )
    uprn_accommodation = models.ForeignKey(
        "ontology.UprnAddress",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="uprn_accommodation",
        db_constraint=False,
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
    volunteer = models.ForeignKey(
        "ontology.MvVolunteer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=False,
        db_column="volunteer_id",
        related_name="accommodation",
    )
    what_type_of_living_space_can_you_offer = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="what_type_of_living_space_can_you_offer",
    )
    wheelchair_accessible = models.BooleanField(
        null=True, blank=True, db_column="wheelchair_accessible"
    )
    who_can_you_accommodate = models.TextField(
        null=True, blank=True, db_column="who_can_you_accommodate"
    )
    hosts = models.ManyToManyField(
        "ontology.MvVolunteer",
        db_table="ontology_sponsor_to_accommodation",
        related_name="accommodations",
        db_constraint=False,
    )
    edited_in_app = models.BooleanField(
        null=True, blank=True, db_column="edited_in_app"
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(null=False, default=False)

    @property
    def ltla_group_info(self) -> GroupInfo | None:
        return GroupInfo.objects.filter(
            ltla_name=self.ltla_name, group_type=GroupType.LOCAL_AUTHORITY
        ).first()

    @property
    def utla_group_info(self) -> GroupInfo | None:
        return GroupInfo.objects.filter(
            utla_name=self.utla_name, group_type=GroupType.LOCAL_AUTHORITY
        ).first()

    def display_link_data(self, linked_from, linked_as) -> LinkedRecordData:
        return LinkedRecordData(
            "accommodations:detail-overview", self.id, self.full_address
        )

    def get_accommodation_requests(self):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        return MvAccommodationRequest.objects.filter(
            Q(accommodation_id__contains=[self.id])
            | Q(primary_accommodation_id=self.id)
        )

    def get_accommodation_requests_restrict_for_user(self, user: User):
        from ontology.models.MvAccommodationRequest import MvAccommodationRequest

        return MvAccommodationRequest.objects.get_for_user(user).filter(
            Q(accommodation_id__contains=[self.id])
            | Q(primary_accommodation_id=self.id)
        )

    def get_postcode(self) -> MvUkPostcode | None:
        if self.postcode_id:
            return MvUkPostcode.objects.filter(id=self.postcode_id).first()
        return None

    def get_volunteer(self) -> MvVolunteer | None:
        if self.volunteer_id:
            return MvVolunteer.objects.filter(id=self.volunteer_id).first()
        return None

    def get_hosts_restrict_for_user(self, user: User):
        if self.hosts:
            return MvVolunteer.objects.get_for_user(user).filter(
                id__in=[h.id for h in self.hosts.all()]
            )
        return MvVolunteer.objects.none()

    def get_visa_applications_restrict_for_user(self, user: User):
        if self.application_unique_application_number:
            uans = self.application_unique_application_number
            return VisaApplication.objects.get_for_user(user).filter(
                application_unique_application_number__in=uans
            )
        return VisaApplication.objects.none()

    class Meta:
        verbose_name = "Accommodation"

    def __str__(self):
        return self.full_address or super().__str__()

    def save(self, *args, **kwargs):
        if not self.is_editable:
            raise ValidationError(
                "Error: Trying to save an MvAccommodation which is not editable"
            )

        self.edited_in_app = True
        super(MvAccommodation, self).save(*args, **kwargs)

    def get_pii_safe_record_name(self) -> str:
        postcode = ""
        mv_postcode = self.get_postcode()
        if mv_postcode and mv_postcode.postcode:
            postcode = mv_postcode.postcode.replace(" ", "")
            postcode = postcode[:4] if len(postcode) >= 4 else postcode

        return postcode
