import uuid

from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import ManyToManyField, Q, TextField, Value
from django.db.models.functions import Coalesce, Concat

from accounts.models import GroupInfo
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models import MvAccommodationRequest, MvInteraction


class ReassignmentRequestQuerySet(models.QuerySet):
    def with_guest_full_names(self):
        return self.annotate(
            guest_full_names=StringAgg(
                Concat(
                    Coalesce(
                        "guests__first_name",
                        Value("", output_field=TextField()),
                        output_field=TextField(),
                    ),
                    Value(" ", output_field=TextField()),
                    Coalesce(
                        "guests__last_name",
                        Value("", output_field=TextField()),
                        output_field=TextField(),
                    ),
                    output_field=TextField(),
                ),
                delimiter=", ",
                ordering=["guests__first_name", "guests__last_name"],
            )
        )


class ReassignmentRequestManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def get_queryset(self):
        return ReassignmentRequestQuerySet(
            self.model, using=self._db
        ).with_guest_full_names()

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return (
            Q(source_ltla_name__overlap=ltla_names)
            & ~Q(source_ltla_name__contained_by=[])
        ) | (Q(destination_ltla_name__in=ltla_names) & ~Q(destination_ltla_name__in=[]))

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return (
            Q(source_utla_name__overlap=utla_names)
            & ~Q(source_utla_name__contained_by=[])
        ) | (Q(destination_utla_name__in=utla_names) & ~Q(destination_utla_name__in=[]))

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        # Identity filter as we don't want to filter by view group name here
        return Q()


class ReassignmentRequestsMadeManager(
    LocalAuthorityPermissionsManagerMixin, models.Manager
):
    def get_queryset(self):
        return ReassignmentRequestQuerySet(
            self.model, using=self._db
        ).with_guest_full_names()

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(source_ltla_name__overlap=ltla_names) & ~Q(
            source_ltla_name__contained_by=[]
        )

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(source_utla_name__overlap=utla_names) & ~Q(
            source_utla_name__contained_by=[]
        )

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        # Identity filter as we don't want to filter by view group name here
        return Q()


class ReassignmentRequestsReceivedManager(
    LocalAuthorityPermissionsManagerMixin, models.Manager
):
    def get_queryset(self):
        return ReassignmentRequestQuerySet(
            self.model, using=self._db
        ).with_guest_full_names()

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(destination_ltla_name__in=ltla_names) & ~Q(
            destination_ltla_name__in=[]
        )

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(destination_utla_name__in=utla_names) & ~Q(
            destination_utla_name__in=[]
        )

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        # Identity filter as we don't want to filter by view group name here
        return Q()


class ReassignmentRequest(models.Model):
    class Outcome(models.TextChoices):
        ACCEPTED = "Accepted", ("Accepted")
        REJECTED = "Rejected", ("Rejected")
        PENDING = "Pending", ("Pending")
        NEEDS_ACCOMMODATION_REQUEST = (
            "Needs Accommodation Request",
            ("Needs Accommodation Request"),
        )

    accommodation_request = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="reassignment_requests",
        null=True,
        blank=True,
        db_column="accommodation_request_id",
        db_constraint=False,
    )
    accommodation_request_title = models.TextField(
        null=True, blank=True, db_column="accommodation_request_title"
    )
    comments = models.TextField(null=True, blank=True, db_column="comments")
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, db_column="created_at"
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="created_by",
        related_name="created_reassignment_requests",
    )
    destination_country = models.TextField(
        null=True, blank=True, db_column="destination_country"
    )
    destination_ltla_code = models.ForeignKey(
        "ontology.UkLocalAuthority",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="destination_ltla_code",
        db_constraint=False,
    )
    destination_ltla_groupid = ArrayField(
        models.TextField(), null=True, blank=True, db_column="destination_ltla_groupid"
    )
    destination_ltla_name = models.TextField(
        null=True, blank=True, db_column="destination_ltla_name"
    )
    destination_utla_code = models.TextField(
        null=True, blank=True, db_column="destination_utla_code"
    )
    destination_utla_groupid = ArrayField(
        models.TextField(), null=True, blank=True, db_column="destination_utla_groupid"
    )
    destination_utla_name = models.TextField(
        null=True, blank=True, db_column="destination_utla_name"
    )
    id = models.TextField(primary_key=True, db_column="id")
    move_date = models.DateField(null=True, blank=True, db_column="move_date")
    outcome = models.TextField(
        null=True, blank=True, db_column="outcome", choices=Outcome.choices
    )
    guests = ManyToManyField(blank=True, to="ontology.MvPerson")
    proposed_at = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, db_column="proposed_at"
    )
    proposed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="proposed_by",
        related_name="proposed_reassignment_requests",
    )
    proposed_by_country = models.TextField(
        null=True, blank=True, db_column="proposed_by_country"
    )
    proposed_by_ltla_code = models.TextField(
        null=True, blank=True, db_column="proposed_by_ltla_code"
    )
    reason = models.TextField(null=True, blank=True, db_column="reason")
    responded_at = models.DateTimeField(null=True, blank=True, db_column="responded_at")
    responded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="responded_by",
        related_name="responded_reassignment_requests",
    )
    actioned_at = models.DateTimeField(null=True, blank=True, db_column="actioned_at")
    source_country = ArrayField(
        models.TextField(), null=True, blank=True, db_column="source_country"
    )
    source_la_group_ids = ArrayField(
        models.TextField(), null=True, blank=True, db_column="source_la_group_ids"
    )
    source_ltla_code = ArrayField(
        models.TextField(), null=True, blank=True, db_column="source_ltla_code"
    )
    source_ltla_name = ArrayField(
        models.TextField(), null=True, blank=True, db_column="source_ltla_name"
    )
    source_utla_code = ArrayField(
        models.TextField(), null=True, blank=True, db_column="source_utla_code"
    )
    source_utla_name = ArrayField(
        models.TextField(), null=True, blank=True, db_column="source_utla_name"
    )
    type = models.TextField(null=True, blank=True, db_column="type")
    viewer_groups = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_groups"
    )

    @property
    def proposed_by_group_info(self) -> GroupInfo | None:
        return GroupInfo.objects.filter(gss_code=self.proposed_by_ltla_code).first()

    # Default manager
    objects = ReassignmentRequestManager()

    # Specialized managers
    made = ReassignmentRequestsMadeManager()
    received = ReassignmentRequestsReceivedManager()

    def get_accommodation_request(self):
        if self.accommodation_request_id:
            return MvAccommodationRequest.objects.filter(
                id=self.accommodation_request_id
            ).first()

        return MvAccommodationRequest.objects.none()

    def formatted_guest_names(self) -> str | None:
        moving_guests = self.guests.all().order_by("full_name")
        if not moving_guests:
            return None

        names = moving_guests[0].get_full_name()
        if len(moving_guests) > 1:
            names_list = [guests.get_full_name() for guests in moving_guests]
            names = ", ".join(names_list[:-1]) + f" and {names_list[-1]}"
        return names

    @classmethod
    def create_reassignment_request(
        cls,
        accommodation_request,
        local_authority,
        reason,
        user,
        guests_to_move,
    ):
        primary_accommodation = accommodation_request.get_primary_accommodation()
        primary_ltla_group_info = (
            primary_accommodation.ltla_group_info if primary_accommodation else None
        )
        proposed_by_country = (
            primary_ltla_group_info.da_name if primary_ltla_group_info else None
        )
        proposed_by_ltla_code = (
            primary_ltla_group_info.gss_code if primary_ltla_group_info else None
        )

        source_country = None
        source_utla_name = None
        utla_group_info = accommodation_request.utla_group_info
        if utla_group_info:
            source_country = set([info.da_name for info in utla_group_info])
            source_utla_name = set([info.utla_gss_code for info in utla_group_info])

        reassignment_request = cls.objects.create(
            id=uuid.uuid4(),
            accommodation_request=accommodation_request,
            accommodation_request_title=accommodation_request.title,
            created_by=user,
            destination_country=local_authority.da_name,
            # destination_ltla_code - not using UkLocalAuthority model
            destination_ltla_name=local_authority.ltla_name,
            destination_utla_code=local_authority.utla_gss_code,
            destination_utla_name=local_authority.utla_name,
            outcome=cls.Outcome.PENDING,
            proposed_by=user,
            proposed_by_country=proposed_by_country,
            proposed_by_ltla_code=proposed_by_ltla_code,
            reason=reason,
            source_country=list(source_country) if source_country else None,
            # source_ltla_code - not using UkLocalAuthority model
            source_ltla_name=accommodation_request.ltla_name,
            source_utla_name=accommodation_request.utla_name,
            source_utla_code=list(source_utla_name) if source_utla_name else None,
        )

        reassignment_request.guests.set(guests_to_move)
        reassignment_request.save()

        MvInteraction.create_interaction(
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
            interaction_type=MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
            linked_accommodation_request=accommodation_request,
            interaction_notes=f"Reassignment request for "
            f"[names_list]{reassignment_request.formatted_guest_names()}"
            f"[names_list_end] "
            f"from {'|'.join(reassignment_request.source_ltla_name)} to "
            f"{reassignment_request.destination_ltla_name}.",
            created_by=user,
            title="Reassignment request",
        )

        return reassignment_request

    def __str__(self):
        ltla_name = (
            self.source_ltla_name[0] if self.source_ltla_name else "Unknown LTLA"
        )

        return (
            f"{self.accommodation_request} "
            f"from {ltla_name} to"
            f" {self.destination_ltla_name} "
            f"with {','.join(list(str(guest) for guest in self.guests.all()))}"
        )
