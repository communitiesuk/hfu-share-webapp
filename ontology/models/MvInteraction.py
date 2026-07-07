import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models


class MvInteraction(models.Model):
    class InteractionContact(models.TextChoices):
        REMATCH_REQUIRED = "Rematch Required"
        REMATCH_REASON_TEMP_ACCOMMODATION = "Guest is in temporary accommodation"
        CENTRAL_CASEWORK_TEAM = (
            "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE"
            "-GENERAL-Central Casework Team"
        )
        UKVI_CASEWORK_TEAM = (
            "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-UKVI -UKVI "
        )
        BORDER_FORCE_PURPOSE = (
            "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-GENERAL-Border Force"
        )
        REMATCH_UNDO_CENTRAL_CASE = "Rematch Reverted by Central Casework Team"
        REMATCH_UNDO = "Rematch Reverted"
        WITHDRAWN_SPONSOR = "Withdrawn Sponsor"
        UNDO_WITHDRAW_SPONSOR = "Reverted Sponsor Withdrawal"
        INDICATED_END_DATE = "Indicated End Date"
        SAFEGUARDING_TEAM_GROUP_ID = "fd6f1237-782b-4879-8718-7aec87de7f7c"
        RETURNED_TO_PROGRAMME = "Returned To Programme"
        LEAVING_PROGRAMME = "Leaving Programme"
        REMATCH_RECORDED = "Rematch Recorded"
        REASSIGNMENT_REQUEST_CREATED = "Reassignment request created"
        REASSIGNMENT_ACCEPTED = "Reassignment accepted"
        REASSIGNMENT_REJECTED = "Reassignment rejected"
        SAFEGUARDING_CHECK_UPDATED = "Safeguarding check updated"
        ACCOMMODATION_SUITABLE_CHECK = "Accommodation is suitable check"
        ACCOMMODATION_EXISTS_CHECK = "Accommodation exists check"
        DBS_AND_SPONSOR_SUITABLE_CHECK = "DBS and sponsor suitable check"
        GUEST_ARRIVED_CHECK = "Guests have arrived in accommodation check"
        GUEST_ARRIVED = "Guests have arrived"
        VISA_APPLICATION_CREATED = "Visa application created"
        VISA_APPLICATION_REFUSED = "Visa application refused"
        VISA_APPLICATION_ISSUED = "Visa application issued"
        RECORD_DEDUPLICATED = "Record deduplicated"
        RECORD_DEDUPLICATION_UNDONE = "Deduplication undone"
        WALES_MIGRATION = "Wales migration"

    attachment = models.TextField(null=True, blank=True, db_column="attachment")
    created_at = models.DateTimeField(
        null=True, blank=True, db_column="created_at", auto_now_add=True
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.DO_NOTHING,
        db_column="created_by",
        null=True,
        blank=True,
    )
    host_relationship_end_date = models.DateField(
        null=True, blank=True, db_column="host_relationship_end_date"
    )
    id = models.TextField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_column="id",
    )
    interaction_contact = models.TextField(
        null=True,
        blank=True,
        db_column="interaction_contact",
        choices=InteractionContact.choices,
    )
    interaction_contact_name = models.TextField(
        null=True, blank=True, db_column="interaction_contact_name"
    )
    interaction_notes = models.TextField(
        null=True, blank=True, db_column="interaction_notes"
    )
    interaction_type = models.TextField(
        null=True, blank=True, db_column="interaction_type"
    )
    linked_accommodation_request = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_constraint=False,
        db_column="linked_accommodation_request",
    )
    linked_match = models.ForeignKey(
        "ontology.EoiHost",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="linked_match_id",
        db_constraint=False,
    )
    linked_sponsor = models.ForeignKey(
        "ontology.MvVolunteer",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="linked_sponsor_id",
        db_constraint=False,
    )
    linked_guest = models.ForeignKey(
        "ontology.MvPerson",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="linked_guest_id",
        db_constraint=False,
    )
    linked_accommodation = models.ForeignKey(
        "ontology.MvAccommodation",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="linked_accommodation_id",
        db_constraint=False,
    )
    linked_old_interaction = models.ForeignKey(
        "ontology.MvInteraction",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_constraint=False,
        db_column="linked_old_interaction_id",
    )
    linked_safeguarding_notification = models.ForeignKey(
        "ontology.SafeguardingNotification",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_constraint=False,
        db_column="linked_safeguarding_notification",
    )
    old_accommodation_request = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="old_accommodation_request",
    )
    title = models.TextField(null=True, blank=True, db_column="title")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )

    @classmethod
    def create_interaction(
        cls,
        interaction_contact,
        interaction_type,
        linked_accommodation_request,
        created_by,
        title,
        interaction_notes=None,
    ):
        return cls.objects.create(
            interaction_contact=interaction_contact,
            interaction_type=interaction_type,
            linked_accommodation_request=linked_accommodation_request,
            interaction_notes=interaction_notes,
            created_by=created_by,
            title=title,
        )

    class Meta:
        verbose_name = "Interaction"

    def __str__(self):
        linked_object = (
            self.linked_accommodation_request
            or self.linked_match
            or self.linked_old_interaction
            or self.linked_safeguarding_notification
            or self.old_accommodation_request
        )
        return f"{self.title} - {self.interaction_type} - {linked_object}"
