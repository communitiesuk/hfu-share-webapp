from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q

from ontology.models import CheckType
from ontology.models.MvInteraction import MvInteraction


class DevCheckV2(models.Model):
    class CheckStatus(models.TextChoices):
        NOT_STARTED = "Not Started", ("Not started")
        IN_PROGRESS = "In Progress", ("In progress")
        PASSED = "Passed", ("Passed")
        FAILED = "Failed", ("Failed")
        NO_LONGER_NEEDED = "No Longer Required", ("No longer needed")
        UNAVAILABLE = "Not Available", ("Not available")

    class SuitabilityFailure(models.TextChoices):
        OVERCROWDED = (
            "OVERCROWDED",
            "Accommodation is overcrowded or at risk of overcrowding",
        )
        NOT_ENOUGH_SPACE = (
            "NOT_ENOUGH_SPACE",
            "Not enough space for guests and their belongings",
        )
        POOR_CONDITION = ("POOR_CONDITION", "Accommodation is in a poor condition")
        UNSUITABLE_FACILITIES = ("UNSUITABLE_FACILITIES", "Facilities are not suitable")
        NO_CONSENT_TO_LIVE_AT_ADDRESS = (
            "NO_CONSENT_TO_LIVE_AT_ADDRESS",
            (
                "The landlord or property owner has not given consent for "
                "guests to live at this address"
            ),
        )
        SPONSOR_NOT_LINKED_TO_ADDRESS = (
            "SPONSOR_NOT_LINKED_TO_ADDRESS",
            "Sponsor is not linked to address",
        )
        SPONSOR_DOES_NOT_LIVE_AT_ADDRESS = (
            "SPONSOR_DOES_NOT_LIVE_AT_ADDRESS",
            "Sponsor does not live at the address stated",
        )

    class SponsorDBSPassedType(models.TextChoices):
        BASIC_DBS = ("BASIC_DBS", "Basic")
        ENHANCED_DBS = ("ENHANCED_DBS", "Enhanced")

    class AccommExistsFailureReason(models.TextChoices):
        DOES_NOT_EXIST = ("DOES_NOT_EXIST", "Address does not exist")
        NOT_RESIDENTIAL = ("NOT_RESIDENTIAL", "This is not a residential address")

    class SponsorDBSFailureReason(models.TextChoices):
        DBS_CHECK_FAILED = (
            "DBS_CHECK_FAILED",
            "DBS check failed",
        )
        NO_CONSENT_TO_BE_SPONSOR = (
            "NO_CONSENT_TO_BE_SPONSOR",
            "This person has not consented to being a sponsor",
        )
        NO_RESPONSE = ("NO_RESPONSE", "Sponsor has not responded to communications")
        SPONSOR_NOT_SUITABLE = (
            "SPONSOR_NOT_SUITABLE",
            "Sponsor is not suitable - other reasons",
        )

    active = models.BooleanField(
        null=True, blank=True, db_column="active", default=True
    )
    check_description = models.TextField(
        null=True, blank=True, db_column="check_description"
    )
    id = models.TextField(primary_key=True, db_column="id")
    check_name = models.TextField(null=True, blank=True, db_column="check_name")
    check_status = models.TextField(
        choices=CheckStatus.choices, null=True, blank=True, db_column="check_status"
    )
    check_subtype = models.TextField(null=True, blank=True, db_column="check_subtype")
    check_type = models.ForeignKey(
        "ontology.CheckType",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="check_type_id",
    )
    note = models.TextField(null=True, blank=True, db_column="note")
    document = models.TextField(null=True, blank=True, db_column="document")
    accommodation = models.ManyToManyField(
        "ontology.MvAccommodation",
        blank=True,
        related_name="checks",
        db_constraint=False,
        db_column="accommodation_id",
    )
    AR = models.ManyToManyField(
        "ontology.MvAccommodationRequest",
        blank=True,
        related_name="checks",
        db_constraint=False,
        db_column="AR_id",
    )
    eoi_host = models.ManyToManyField(
        "ontology.EoiHost", blank=True, related_name="checks", db_column="eoi_host_id"
    )
    group = models.ManyToManyField(
        "ontology.MvGroup",
        blank=True,
        related_name="checks",
        db_constraint=False,
        db_column="group_id",
    )
    person = models.ManyToManyField(
        "ontology.MvPerson",
        blank=True,
        related_name="checks",
        db_constraint=False,
        db_column="person_id",
    )
    sponsor = models.ManyToManyField(
        "ontology.MvVolunteer",
        related_name="checks",
        blank=True,
        db_constraint=False,
        db_column="sponsor_id",
    )
    ltla_code = models.ManyToManyField(
        "ontology.UkLocalAuthority",
        related_name="+",
        blank=True,
        db_constraint=False,
        db_column="ltla_code",
    )
    create_at = models.DateTimeField(null=True, blank=True, db_column="create_at")
    create_by = models.TextField(null=True, blank=True, db_column="create_by")

    last_updated_at = models.DateTimeField(
        null=True, blank=True, db_column="last_updated_at"
    )
    last_updated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="last_updated_by",
        related_name="checks_last_updated",
    )

    utla_code = ArrayField(
        models.TextField(), null=True, blank=True, db_column="utla_code"
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )

    def __str__(self):
        return f"{self.id}, {self.check_type}"

    def get_check_subtype_label(self):
        if not self.check_subtype:
            return ""

        if self.check_subtype in self.SuitabilityFailure:
            return self.SuitabilityFailure[self.check_subtype].label

        if self.check_subtype in self.AccommExistsFailureReason:
            return self.AccommExistsFailureReason[self.check_subtype].label

        if self.check_subtype in self.SponsorDBSFailureReason:
            return self.SponsorDBSFailureReason[self.check_subtype].label

        if (
            validated_type := validate_sponsor_dbs_passed_subtype(self.check_subtype)
        ) in self.SponsorDBSPassedType:
            return self.SponsorDBSPassedType[validated_type].label

        return self.check_subtype

    def get_check_failed_title(self):
        if not self.check_type:
            return None
        if str(self.check_type.id) == "1":
            return "Accommodation exists check failed"
        if str(self.check_type.id) == "2":
            return "Accommodation suitable check failed"
        if str(self.check_type.id) == "3":
            return "DBS check and Sponsor suitable check failed"
        return getattr(self.check_type, "check_name", str(self.check_type))

    def get_related_ars_to_sponsor_check(self):
        from ontology.models import MvAccommodationRequest

        sponsor_ids = list(self.sponsor.values_list("id", flat=True))

        if len(sponsor_ids) > 0:
            return (
                MvAccommodationRequest.objects.filter(
                    Q(sponsor_id__overlap=sponsor_ids)
                    | Q(active_host_id__in=sponsor_ids)
                    | Q(primary_sponsor_id__in=sponsor_ids)
                )
                .exclude(sponsor_withdrawn__contains=sponsor_ids)
                .values_list("id", flat=True)
            )

        return []

    def get_related_ars_to_accommodation_check(self):
        from ontology.models import MvAccommodationRequest

        accommodation_ids = list(self.accommodation.values_list("id", flat=True))

        if len(accommodation_ids) > 0:
            return MvAccommodationRequest.objects.filter(
                Q(primary_accommodation_id__in=accommodation_ids)
                | Q(accommodation_id__overlap=accommodation_ids)
                | Q(bridging_accommodation_id__in=accommodation_ids)
                | Q(temporary_accommodation_id__in=accommodation_ids)
            ).values_list("id", flat=True)

        return []

    def get_related_ars_to_group_check(self):
        from ontology.models import MvAccommodationRequest

        group_ids = list(self.group.values_list("id", flat=True))

        if len(group_ids) > 0:
            return MvAccommodationRequest.objects.filter(
                group_id__in=group_ids
            ).values_list("id", flat=True)

        return []

    def get_related_ar_ids(self):
        ar_ids = set(self.AR.values_list("id", flat=True))

        if (
            self.check_type is not None
            and self.check_type.id == CheckType.Id.SPONSOR_DBS
        ):
            ar_ids.update(self.get_related_ars_to_sponsor_check())

        if (
            self.check_type is not None
            and self.check_type.id == CheckType.Id.ACCOMM_EXISTS
        ):
            ar_ids.update(self.get_related_ars_to_accommodation_check())

        if (
            self.check_type is not None
            and self.check_type.id == CheckType.Id.GROUP_ARRIVED
        ):
            ar_ids.update(self.get_related_ars_to_group_check())

        return set(ar_ids)

    def determine_interaction_type(self) -> MvInteraction.InteractionContact:
        if not self.check_type_id:
            return MvInteraction.InteractionContact.SAFEGUARDING_CHECK_UPDATED

        if self.check_type_id == CheckType.Id.ACCOMM_EXISTS:
            return MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK

        if self.check_type_id == CheckType.Id.ACCOMM_SUITABLE:
            return MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK

        if self.check_type_id == CheckType.Id.SPONSOR_DBS:
            return MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK

        if self.check_type_id == CheckType.Id.GROUP_ARRIVED:
            return MvInteraction.InteractionContact.GUEST_ARRIVED_CHECK

        return MvInteraction.InteractionContact.SAFEGUARDING_CHECK_UPDATED

    def determine_interaction_title(
        self, interaction_type: MvInteraction.InteractionContact
    ) -> str:
        if (
            interaction_type
            == MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK
        ):
            if self.check_status == self.CheckStatus.FAILED:
                return interaction_type + ": failed"

            if (
                self.check_subtype
                and self.check_subtype == self.SponsorDBSPassedType.BASIC_DBS
            ):
                return interaction_type + ": Basic DBS"

            if (
                self.check_subtype
                and self.check_subtype == self.SponsorDBSPassedType.ENHANCED_DBS
            ):
                return interaction_type + ": Enhanced DBS"

        return interaction_type

    def determine_interaction_notes(
        self, interaction_type: MvInteraction.InteractionContact, updated_at
    ) -> str:
        status = self.get_check_status_display().lower()
        date = updated_at.strftime("%-d %B %Y")

        if (
            interaction_type
            == MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK
        ):
            if self.check_status == self.CheckStatus.FAILED:
                interaction_notes = (
                    f"Sponsor suitable check failed on {date}. "
                    f"Reason: {self.get_check_subtype_label()}."
                )

                if self.note:
                    interaction_notes += f"\nComments: {self.note}"

                return interaction_notes

            if (
                self.check_subtype
                and self.check_subtype == self.SponsorDBSPassedType.BASIC_DBS
            ):
                return f"Basic DBS check: {status} on {date}"

            if (
                self.check_subtype
                and self.check_subtype == self.SponsorDBSPassedType.ENHANCED_DBS
            ):
                return f"Enhanced DBS check: {status} on {date}"

        return interaction_type + f": {status} on {date}"

    def create_interactions_for_check_update(self, source_ar, author, updated_at):
        from ontology.models import MvAccommodationRequest

        related_ar_ids = self.get_related_ar_ids()
        related_ars = MvAccommodationRequest.objects.filter(
            id__in=related_ar_ids,
        )

        interaction_type = self.determine_interaction_type()
        interaction_notes = self.determine_interaction_notes(
            interaction_type, updated_at
        )
        title = self.determine_interaction_title(interaction_type)

        for ar in related_ars:
            MvInteraction.create_interaction(
                interaction_contact=interaction_type,
                interaction_type=interaction_type,
                linked_accommodation_request=ar,
                interaction_notes=interaction_notes,
                # Interaction is created by the system if it is not the AR which the
                # user updated the check via. Hence, set created_by to None.
                created_by=author if ar.id == source_ar.id else None,
                title=title,
            )


def validate_safeguarding_status(safeguarding_status):
    status = str(
        safeguarding_status.upper().replace(" ", "_").replace("REQUIRED", "NEEDED")
    )
    try:
        validated_status = getattr(DevCheckV2.CheckStatus, status)
    except AttributeError:
        # Unexpected value - assume not started
        validated_status = DevCheckV2.CheckStatus.UNAVAILABLE
    return validated_status


def validate_sponsor_dbs_passed_subtype(check_subtype: str | None):
    if not check_subtype:
        return None

    status = str(check_subtype.upper().replace(" ", "_"))
    # Handle legacy subtypes which didn't suffix "DBS"
    if not status.endswith("_DBS"):
        status = status + "_DBS"

    try:
        validated_status = getattr(DevCheckV2.SponsorDBSPassedType, status)
    except AttributeError:
        # Unexpected value - return no subtype
        validated_status = None
    return validated_status
