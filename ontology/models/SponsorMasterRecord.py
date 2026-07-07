from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import ManyToManyField


class SponsorMasterRecord(models.Model):
    adverse_hit = ArrayField(models.TextField(), null=True, db_column="adverse_hit")
    age = ArrayField(models.TextField(), null=True, db_column="age")
    comments = ArrayField(models.TextField(), null=True, db_column="comments")
    record_id = models.TextField(primary_key=True, db_column="record_id")
    date_of_birth = ArrayField(models.TextField(), null=True, db_column="date_of_birth")
    email = ArrayField(models.TextField(), null=True, db_column="email")
    expiry_date_id = ArrayField(
        models.TextField(), null=True, db_column="expiry_date_id"
    )
    family_situation = ArrayField(
        models.TextField(), null=True, db_column="family_situation"
    )
    first_name = ArrayField(models.TextField(), null=True, db_column="first_name")
    flag_unsuitable = ArrayField(
        models.TextField(), null=True, db_column="flag_unsuitable"
    )
    full_name = ArrayField(models.TextField(), null=True, db_column="full_name")
    gwf = ArrayField(models.TextField(), null=True, db_column="gwf")
    has_background_check = ArrayField(
        models.TextField(), null=True, db_column="has_background_check"
    )
    has_identity_card = ArrayField(
        models.TextField(), null=True, db_column="has_identity_card"
    )
    hosting_duration = ArrayField(
        models.TextField(), null=True, db_column="hosting_duration"
    )
    id = ArrayField(models.TextField(), null=True, db_column="id")
    Individual_or_Organisation = ArrayField(
        models.TextField(), null=True, db_column="Individual_or_Organisation"
    )
    is_eoi = ArrayField(models.TextField(), null=True, db_column="is_eoi")
    is_person_of_interest = ArrayField(
        models.TextField(), null=True, db_column="is_person_of_interest"
    )
    is_principal = ArrayField(models.TextField(), null=True, db_column="is_principal")
    is_sponsor = ArrayField(models.TextField(), null=True, db_column="is_sponsor")
    issue_date_id = ArrayField(models.TextField(), null=True, db_column="issue_date_id")
    issuing_authority_of_id = ArrayField(
        models.TextField(), null=True, db_column="issuing_authority_of_id"
    )
    last_name = ArrayField(models.TextField(), null=True, db_column="last_name")
    national_identity_card_number = ArrayField(
        models.TextField(), null=True, db_column="national_identity_card_number"
    )
    nationality = ArrayField(models.TextField(), null=True, db_column="nationality")
    notional_data = ArrayField(models.TextField(), null=True, db_column="notional_data")
    organization_name = ArrayField(
        models.TextField(), null=True, db_column="organization_name"
    )
    organization_type = ArrayField(
        models.TextField(), null=True, db_column="organization_type"
    )
    other_nationalities = ArrayField(
        models.TextField(), null=True, db_column="other_nationalities"
    )
    passport_details = ArrayField(
        models.TextField(), null=True, db_column="passport_details"
    )
    phone_number = ArrayField(models.TextField(), null=True, db_column="phone_number")
    previous_id = ArrayField(models.TextField(), null=True, db_column="previous_id")
    principal_record = models.ForeignKey(
        "ontology.MvVolunteer",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_column="principal_record_id",
    )
    residential_postcodes = ArrayField(
        models.TextField(), null=True, db_column="residential_postcodes"
    )
    response_id = ArrayField(models.TextField(), null=True, db_column="response_id")
    sex = ArrayField(models.TextField(), null=True, db_column="sex")
    source = ArrayField(models.TextField(), null=True, db_column="source")
    sponsor_status = ArrayField(
        models.TextField(), null=True, db_column="sponsor_status"
    )
    sponsorship_certification_number = ArrayField(
        models.TextField(), null=True, db_column="sponsorship_certification_number"
    )
    survey_response = ArrayField(
        models.TextField(), null=True, db_column="survey_response"
    )
    type = models.TextField(null=True, db_column="type")
    application_unique_application_number = ArrayField(
        models.TextField(), null=True, db_column="application_unique_application_number"
    )
    unsubscribed = ArrayField(models.TextField(), null=True, db_column="unsubscribed")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )

    sponsors = ManyToManyField(
        "ontology.MvVolunteer",
        db_table="ontology_sponsor_to_master_record",
        related_name="master_record",
    )
