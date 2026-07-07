from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import QuerySet

from ontology.models import DevCheckV2


class EoiHost(models.Model):
    checks: QuerySet[DevCheckV2]

    agree_to_be_contacted = models.TextField(
        null=True, db_column="agree_to_be_contacted"
    )
    contact_number = models.TextField(null=True, db_column="contact_number")
    created_date = models.DateTimeField(null=True, db_column="created_date")
    datasource = ArrayField(models.TextField(), null=True, db_column="datasource")
    email = models.TextField(null=True, db_column="email")
    full_name = models.TextField(null=True, db_column="full_name")
    host_id = models.TextField(primary_key=True, db_column="host_id")
    hosting_duration = models.IntegerField(null=True, db_column="hosting_duration")
    Individual_or_Organisation = models.TextField(
        null=True, db_column="Individual_or_Organisation"
    )
    existing_sponsor = models.BooleanField(null=True, db_column="existing_sponsor")
    last_updated_date = models.DateTimeField(null=True, db_column="last_updated_date")
    matched_accommodation_request = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_column="matched_accommodation_request_id",
    )
    notional_data = models.BooleanField(null=True, db_column="notional_data")
    number_failed_checks = models.BigIntegerField(
        null=True, db_column="number_failed_checks"
    )
    old_matched_accommodation_request_id = models.TextField(
        null=True, db_column="old_matched_accommodation_request_id"
    )
    organization_name = models.TextField(null=True, db_column="organization_name")
    organization_type = models.TextField(null=True, db_column="organization_type")
    privacy_agreement = models.TextField(null=True, db_column="privacy_agreement")
    response_id = ArrayField(models.TextField(), null=True, db_column="response_id")
    sponsor = models.ManyToManyField(
        "ontology.MvVolunteer", related_name="+", db_column="sponsor_id"
    )
    survey_response = models.TextField(null=True, db_column="survey_response")
    unsubscribed = models.BooleanField(null=True, db_column="unsubscribed")
    unsuitable = models.BooleanField(null=True, db_column="unsuitable")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )
