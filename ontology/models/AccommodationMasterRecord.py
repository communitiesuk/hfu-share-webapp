from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import ManyToManyField


class AccommodationMasterRecord(models.Model):
    accommodation_availability = ArrayField(
        models.TextField(), null=True, db_column="accommodation_availability"
    )
    accommodation_provider = ArrayField(
        models.TextField(), null=True, db_column="accommodation_provider"
    )
    accommodation_provider_type = ArrayField(
        models.TextField(), null=True, db_column="accommodation_provider_type"
    )
    actioned_at = models.DateTimeField(null=True, db_column="actioned_at")
    allow_pet = ArrayField(models.TextField(), null=True, db_column="allow_pet")
    application_unique_application_number = ArrayField(
        models.TextField(), null=True, db_column="application_unique_application_number"
    )
    confidence_level = models.TextField(null=True, db_column="confidence_level")
    confidence_score = models.FloatField(null=True, db_column="confidence_score")
    country = ArrayField(models.TextField(), null=True, db_column="country")
    full_address = ArrayField(models.TextField(), null=True, db_column="full_address")
    geohash = ArrayField(models.TextField(), null=True, db_column="geohash")
    gwf = ArrayField(models.TextField(), null=True, db_column="gwf")
    host_id = ArrayField(models.TextField(), null=True, db_column="host_id")
    id = ArrayField(models.TextField(), null=True, db_column="id")
    is_accommodation = ArrayField(
        models.TextField(), null=True, db_column="is_accommodation"
    )
    is_eoi = ArrayField(models.TextField(), null=True, db_column="is_eoi")
    is_principal = ArrayField(models.TextField(), null=True, db_column="is_principal")
    is_residential = ArrayField(
        models.TextField(), null=True, db_column="is_residential"
    )
    local_authority = ArrayField(
        models.TextField(), null=True, db_column="local_authority"
    )
    ltla_name = ArrayField(models.TextField(), null=True, db_column="ltla_name")
    notional_data = ArrayField(models.TextField(), null=True, db_column="notional_data")
    number_adults = ArrayField(models.TextField(), null=True, db_column="number_adults")
    number_children = ArrayField(
        models.TextField(), null=True, db_column="number_children"
    )
    number_of_double_rooms_available = ArrayField(
        models.TextField(), null=True, db_column="number_of_double_rooms_available"
    )
    number_of_single_rooms = ArrayField(
        models.TextField(), null=True, db_column="number_of_single_rooms"
    )
    postcode = ArrayField(models.TextField(), null=True, db_column="postcode")
    principal_record = models.ForeignKey(
        "ontology.MvAccommodation",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_column="principal_record_id",
    )
    record_id = models.TextField(primary_key=True, db_column="record_id")
    reference = ArrayField(models.TextField(), null=True, db_column="reference")
    response_id = ArrayField(models.TextField(), null=True, db_column="response_id")
    source = ArrayField(models.TextField(), null=True, db_column="source")
    sponsorship_certification_number = ArrayField(
        models.TextField(), null=True, db_column="sponsorship_certification_number"
    )
    submission_guid = ArrayField(
        models.TextField(), null=True, db_column="submission_guid"
    )
    type = models.TextField(null=True, db_column="type")
    unsubscribed = ArrayField(models.TextField(), null=True, db_column="unsubscribed")
    unsuitable = ArrayField(models.TextField(), null=True, db_column="unsuitable")
    uprn_address = models.TextField(null=True, db_column="uprn_address")
    utla_name = ArrayField(models.TextField(), null=True, db_column="utla_name")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )
    volunteer_id = ArrayField(models.TextField(), null=True, db_column="volunteer_id")
    what_type_of_living_space_can_you_offer = ArrayField(
        models.TextField(),
        null=True,
        db_column="what_type_of_living_space_can_you_offer",
    )
    who_can_you_accommodate = ArrayField(
        models.TextField(), null=True, db_column="who_can_you_accommodate"
    )

    accommodations = ManyToManyField(
        "ontology.MvAccommodation",
        db_table="ontology_accommodation_to_master_record",
        related_name="master_record",
    )
