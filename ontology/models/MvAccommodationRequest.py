import logging
from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from dateutil.tz import tzutc
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import CharField, OuterRef, Q, QuerySet
from django.db.models.expressions import Func
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from accounts.models import GroupInfo, User
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models import CheckType, DevCheckV2
from ontology.models.DevCheckV2 import validate_sponsor_dbs_passed_subtype
from ontology.models.EoiHost import EoiHost
from ontology.models.MvAccommodation import MvAccommodation
from ontology.models.MvGroup import MvGroup
from ontology.models.MvPerson import MvPerson, get_person_age_sort_key
from ontology.models.MvVolunteer import MvVolunteer
from ontology.models.SponsorshipCertificationForm import SponsorshipCertificationForm
from ontology.models.VisaApplication import VisaApplication
from ontology.utils import LinkedRecordData

logger = logging.getLogger(__name__)


class MvAccommodationRequestQueryset(models.QuerySet):
    def _la_names(self, la_field_name: str) -> QuerySet[str]:
        flatted_column_name = f"{la_field_name}_flat"
        return (
            self.annotate(
                **{
                    flatted_column_name: Func(
                        models.F(la_field_name),
                        function="UNNEST",
                        output_field=CharField(),
                    )
                }
            )
            .values_list(flatted_column_name, flat=True)
            .distinct()
            .order_by(flatted_column_name)
        )

    def ltla_names(self) -> QuerySet[str]:
        return self._la_names("ltla_name")

    def utla_names(self) -> QuerySet[str]:
        return self._la_names("utla_name")

    def with_checks(self):
        check_ids_subquery = DevCheckV2.objects.filter(
            # Group checks
            Q(
                # If match group_id
                group__id=OuterRef("group_id"),
                check_type__id=CheckType.Id.GROUP_ARRIVED,
            )
            | Q(
                # Checks of type GROUP_ARRIVED specific to this AR
                AR__id=OuterRef("id"),
                check_type__id=CheckType.Id.GROUP_ARRIVED,
            )
            # Sponsor checks
            | Q(
                # In sponsor_id checks - excluding withdrawn sponsors
                Q(sponsor__id__any=OuterRef("sponsor_id"))
                & ~Q(sponsor__id__any=OuterRef("sponsor_withdrawn"))
                & Q(check_type__id=CheckType.Id.SPONSOR_DBS)
            )
            | Q(
                # primary_sponsor_id or active_host_id checks - excluding withdrawn
                Q(
                    sponsor__id__in=[
                        OuterRef("primary_sponsor_id"),
                        OuterRef("active_host_id"),
                    ]
                )
                & ~Q(sponsor__id__any=OuterRef("sponsor_withdrawn"))
                & Q(check_type__id=CheckType.Id.SPONSOR_DBS)
            )
            # Accommodation checks
            | Q(
                # accommodation_id suitable checks - specific to this AR
                accommodation__id__any=OuterRef("accommodation_id"),
                check_type__id=CheckType.Id.ACCOMM_SUITABLE,
                AR__id=OuterRef("id"),
            )
            | Q(
                # accommodation_id exists checks - universal for all ARs
                accommodation__id__any=OuterRef("accommodation_id"),
                check_type__id=CheckType.Id.ACCOMM_EXISTS,
            )
            | Q(
                # bridging, temporary, and primary suitable checks - specific to this AR
                accommodation__id__in=[
                    OuterRef("bridging_accommodation_id"),
                    OuterRef("temporary_accommodation_id"),
                    OuterRef("primary_accommodation_id"),
                ],
                check_type__id=CheckType.Id.ACCOMM_SUITABLE,
                AR__id=OuterRef("id"),
            )
            | Q(
                # bridging, temporary, and primary exists checks - universal for all ARs
                accommodation__id__in=[
                    OuterRef("bridging_accommodation_id"),
                    OuterRef("temporary_accommodation_id"),
                    OuterRef("primary_accommodation_id"),
                ],
                check_type__id=CheckType.Id.ACCOMM_EXISTS,
            )
        )

        # Return queryset with prefetched check objects
        return self.annotate(
            check_ids=ArraySubquery(check_ids_subquery.values("id").distinct()),
            check_subtypes=ArraySubquery(
                check_ids_subquery.filter(
                    check_status=DevCheckV2.CheckStatus.FAILED,
                    active=True,
                )
                .values("check_subtype")
                .distinct()
            ),
        )


class MvAccommodationRequestManager(
    LocalAuthorityPermissionsManagerMixin, models.Manager
):
    def get_queryset(self):
        return MvAccommodationRequestQueryset(self.model, using=self._db)

    def with_checks(self):
        return self.get_queryset().with_checks()

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(ltla_name__overlap=ltla_names) & ~Q(ltla_name__contained_by=[])

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(utla_name__overlap=utla_names) & ~Q(utla_name__contained_by=[])

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class MvAccommodationRequest(models.Model):
    checks: QuerySet[DevCheckV2]

    class ClosedReason(models.TextChoices):
        RETURNED_TO_UKRAINE = (
            "Return to Ukraine",
            _("Returned to Ukraine"),
        )
        RETURNED_TO_ANOTHER_COUNTRY = (
            "Return to other country",
            _("Returned to another country (not Ukraine)"),
        )
        FOUND_INDEPENDENT_PRIVATE_ACCOMMODATION = (
            "Found private independent accommodation",
            _("Found independent private accommodation"),
        )
        CHOSE_NOT_TO_TRAVEL_TO_UK = (
            "Chose not to travel to UK",
            _("Chose not to travel to UK"),
        )
        ENTERED_SOCIAL_HOUSING = (
            "Entered Social Housing",
            _("Entered social housing"),
        )
        MOVED_INTO_CLOSE_FAMILY_MEMBER_ACCOMMODATION = (
            "Moved into close family member accommodation",
            _("Moved into close family member accommodation"),
        )
        OTHER = ("Other", _("Other (please comment)"))

    class Status(models.TextChoices):
        ACCOMMODATION_ASSIGNED = "Accommodation Assigned", _("Accommodation assigned")
        MISSING_ACCOMMODATION = "Missing Accommodation", _("Missing accommodation")
        ARRIVAL_CONFIRMED = "Arrival Confirmed", _("Arrival confirmed")

    class ChecksStatus(models.TextChoices):
        CHECKS_REQUIRED = "Checks Required", _("Checks required")
        PRE_ARRIVAL_CHECKS_COMPLETE = (
            "Pre-Arrival Checks Complete",
            _("Pre-Arrival checks complete"),
        )
        CHECKS_PARTIALLY_COMPLETED = (
            "Checks Partially Completed",
            _("Checks partially completed"),
        )
        CHECKS_COMPLETED = "Checks Completed", _("Checks completed")
        SOME_CHECKS_FAILED = "Some Checks Failed", _("Some checks failed")
        CLOSED_DUPLICATE = "Closed - Duplicate", _("Closed - Duplicate")
        CLOSED_LEFT_PROGRAMME = "Closed - left programme", _("Closed - Left programme")
        CLOSED_EMPTY = "Closed - Empty", _("Closed - Empty")
        REMATCH_REQUIRED = "Rematch Required", _("Rematch required")
        IN_TEMPORARY_ACCOMMODATION = (
            "In Temporary Accommodation",
            _("In temporary accommodation"),
        )
        CANCELLED = "Cancelled", _("Cancelled")

    CLOSED_STATUSES = (
        ChecksStatus.CLOSED_LEFT_PROGRAMME,
        ChecksStatus.CLOSED_DUPLICATE,
        ChecksStatus.CANCELLED,
        ChecksStatus.CLOSED_EMPTY,
    )

    class SafeguardingStatus(models.TextChoices):
        NO_NOTIFICATIONS = (
            "No Safeguarding Notifications",
            _("No safeguarding notifications"),
        )
        NO_OPEN_NOTIFICATIONS = (
            "No Open Safeguarding Notifications",
            _("No open safeguarding notifications"),
        )
        ACTIVE_NOTIFICATIONS = (
            "Active Safeguarding Notifications",
            _("Active safeguarding notifications"),
        )
        UNASSIGNED_NOTIFICATIONS = (
            "Unassigned Safeguarding Notifications",
            _("Unassigned safeguarding notifications"),
        )

    objects = MvAccommodationRequestManager()

    accommodation_details_confirmed = models.BooleanField(
        null=True, blank=True, db_column="accommodation_details_confirmed"
    )
    accommodation_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="accommodation_id",
        verbose_name="Accommodation ID",
    )
    old_split_accommodation_request = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="old_split_accommodation_request",
        db_constraint=False,
    )
    status = models.TextField(
        null=True, blank=True, db_column="status", choices=Status.choices
    )
    active_eoi_host = models.ForeignKey(
        "ontology.EoiHost",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="active_eoi_host",
        db_constraint=False,
        verbose_name="Active EOI host",
    )
    active_host = models.ForeignKey(
        "ontology.MvVolunteer",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="active_host",
        db_constraint=False,
    )
    linked_adverse_rematch = models.BooleanField(
        null=True, blank=True, db_column="linked_adverse_rematch"
    )
    assignee = models.TextField(null=True, blank=True, db_column="assignee")
    bridging_accommodation_id = models.TextField(
        null=True,
        blank=True,
        db_column="bridging_accommodation_id",
        verbose_name="Bridging accommodation ID",
    )
    bridging_accommodation_needed = models.BooleanField(
        null=True, blank=True, db_column="bridging_accommodation_needed"
    )
    cancellation_reason = models.TextField(
        null=True, blank=True, db_column="cancellation_reason"
    )
    central_case_flag = models.BooleanField(
        null=True, blank=True, db_column="central_case_flag"
    )
    checks_required = ArrayField(
        models.TextField(), null=True, blank=True, db_column="checks_required"
    )
    comment = models.TextField(null=True, blank=True, db_column="comment")
    confirmed_arrival_date = models.DateField(
        null=True, blank=True, db_column="confirmed_arrival_date"
    )
    created_by = models.TextField(null=True, blank=True, db_column="created_by")
    date_from = models.DateField(null=True, blank=True, db_column="date_from")
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    date_till = models.DateField(null=True, blank=True, db_column="date_till")
    edited_end_date_at = models.DateTimeField(
        null=True, blank=True, db_column="edited_end_date_at"
    )
    is_uam = models.BooleanField(
        null=True, blank=True, db_column="is_uam", verbose_name="Is UAM"
    )
    is_uam_edited_time = models.DateTimeField(
        null=True,
        blank=True,
        db_column="is_uam_edited_time",
        verbose_name="Is UAM edited time",
    )
    expected_check_in_date_confirmed = models.BooleanField(
        null=True, blank=True, db_column="expected_check_in_date_confirmed"
    )
    expected_end_date = models.DateField(
        null=True, blank=True, db_column="expected_end_date"
    )
    expected_end_date_is_autogenerated = models.BooleanField(
        null=True, blank=True, db_column="expected_end_date_is_autogenerated"
    )
    first_arrival_date = models.DateField(
        null=True, blank=True, db_column="first_arrival_date"
    )
    group_details_confirmed = models.BooleanField(
        null=True, blank=True, db_column="group_details_confirmed"
    )
    group = models.ForeignKey(
        "ontology.MvGroup",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_constraint=False,
        db_column="group_id",
    )
    has_uk_consent_doc = models.BooleanField(
        null=True,
        blank=True,
        db_column="has_uk_consent_doc",
        verbose_name="Has UK consent doc",
    )
    has_ukraine_consent_doc = models.BooleanField(
        null=True,
        blank=True,
        db_column="has_ukraine_consent_doc",
        verbose_name="Has Ukraine consent doc",
    )
    have_notified_flag = models.BooleanField(
        null=True, blank=True, db_column="have_notified_flag"
    )
    id = models.TextField(primary_key=True, db_column="id", verbose_name="ID")
    in_temporary_accommodation = models.BooleanField(
        null=True, blank=True, db_column="in_temporary_accommodation"
    )
    is_duplicate = models.TextField(null=True, blank=True, db_column="is_duplicate")
    is_eoi_host = models.BooleanField(
        null=True, blank=True, db_column="is_eoi_host", verbose_name="Is EOI host"
    )
    is_principal = models.BooleanField(null=True, blank=True, db_column="is_principal")
    la_priority = models.IntegerField(
        null=True, blank=True, db_column="la_priority", verbose_name="LA priority"
    )
    la_priority_string = models.TextField(
        null=True,
        blank=True,
        db_column="la_priority_string",
        verbose_name="LA priority string",
    )
    last_modified_by_org = models.TextField(
        null=True,
        blank=True,
        db_column="last_modified_by_org",
        verbose_name="Last modified by organisation",
    )
    last_modified_at = models.DateTimeField(
        null=True, blank=True, db_column="last_modified_at"
    )
    last_modified_by = models.TextField(
        null=True, blank=True, db_column="last_modified_by"
    )
    latest_application_date = models.DateField(
        null=True, blank=True, db_column="latest_application_date"
    )
    linked_adverse_hit = models.BooleanField(
        null=True, blank=True, db_column="linked_adverse_hit"
    )
    ltla_name = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="ltla_name",
        verbose_name="LTLA name",
    )
    # Array of LTLA code IDs
    ltla_code_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="ltla_code",
        verbose_name="LTLA code ID",
    )
    # The actual ManyToManyField for ltla_code
    ltla_code = models.ManyToManyField(
        "ontology.UkLocalAuthority",
        blank=True,
        related_name="+",
        db_column="ltla_code",
        verbose_name="LTLA code",
    )
    match_id = models.TextField(
        null=True, blank=True, db_column="match_id", verbose_name="Match ID"
    )
    max_age = models.IntegerField(null=True, blank=True, db_column="max_age")
    merged_accommodation_request = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="merged_accommodation_request",
    )
    min_age = models.IntegerField(null=True, blank=True, db_column="min_age")
    notional_data = models.BooleanField(
        null=True, blank=True, db_column="notional_data"
    )
    number_of_people = models.BigIntegerField(
        null=True, blank=True, db_column="number_of_people"
    )
    person_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="person_id",
        verbose_name="Person ID",
    )
    postcode = ArrayField(
        models.TextField(), null=True, blank=True, db_column="postcode"
    )
    # Array of Previous Accommodation IDs
    previous_accommodation_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="previous_accommodation",
        verbose_name="Previous accommodation ID",
    )
    # The actual ManyToManyField for previous accommodations
    previous_accommodation = models.ManyToManyField(
        "ontology.MvAccommodation",
        blank=True,
        related_name="+",
        db_column="previous_accommodation",
    )
    # Array of Previous EOI Host IDs
    previous_eoi_host_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="previous_eoi_hosts",
        verbose_name="Previous EOI host ID",
    )
    # The actual ManyToManyField for previous EOI hosts
    previous_eoi_hosts = models.ManyToManyField(
        "ontology.EoiHost",
        related_name="+",
        blank=True,
        db_column="previous_eoi_hosts",
        db_constraint=False,
        verbose_name="Previous EOI hosts",
    )
    previous_ids = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="previous_ids",
        verbose_name="Previous IDs",
    )
    primary_accommodation = models.ForeignKey(
        "ontology.MvAccommodation",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="primary_accommodation_id",
        db_constraint=False,
    )
    primary_contact_can_be_contacted_by_phone = models.TextField(
        null=True, blank=True, db_column="primary_contact_can_be_contacted_by_phone"
    )
    primary_contact_email = ArrayField(
        models.TextField(), null=True, blank=True, db_column="primary_contact_email"
    )
    primary_contact_email_after_decision = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="primary_contact_email_after_decision",
    )
    primary_contact_email_for_decision = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="primary_contact_email_for_decision",
    )
    primary_contact_email_for_questions = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="primary_contact_email_for_questions",
    )
    primary_contact_first_name = models.TextField(
        null=True, blank=True, db_column="primary_contact_first_name"
    )
    primary_contact_last_name = models.TextField(
        null=True, blank=True, db_column="primary_contact_last_name"
    )
    primary_contact_phone = ArrayField(
        models.TextField(), null=True, blank=True, db_column="primary_contact_phone"
    )
    primary_sponsor = models.ForeignKey(
        "ontology.MvVolunteer",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="primary_sponsor_id",
        db_constraint=False,
    )
    checks_status = models.TextField(
        null=True, blank=True, db_column="checks_status", choices=ChecksStatus.choices
    )
    safeguarding_status = models.TextField(
        null=True,
        blank=True,
        db_column="safeguarding_status",
        choices=SafeguardingStatus.choices,
    )
    sponsor_background_check_confirmed = models.BooleanField(
        null=True, blank=True, db_column="sponsor_background_check_confirmed"
    )
    sponsor_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="sponsor_id",
        verbose_name="Sponsor ID",
    )
    # Array of SponsorshipCertificationForm IDs
    sponsorship_certification_number_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="sponsorship_certification_number",
        verbose_name="Sponsorship certification application number",
    )
    temporary_accommodation_id = models.TextField(
        null=True,
        blank=True,
        db_column="temporary_accommodation_id",
        verbose_name="Temporary accommodation ID",
    )
    title = models.TextField(null=True, blank=True, db_column="title")
    uk_consent_doc = models.TextField(
        null=True, blank=True, db_column="uk_consent_doc", verbose_name="UK consent doc"
    )
    uk_consent_doc_edited_time = models.DateTimeField(
        null=True,
        blank=True,
        db_column="uk_consent_doc_edited_time",
        verbose_name="UK consent doc edited time",
    )
    ukraine_consent_doc_edited_time = models.DateTimeField(
        null=True, blank=True, db_column="ukraine_consent_doc_edited_time"
    )
    ukraine_consent_doc = models.TextField(
        null=True, blank=True, db_column="ukraine_consent_doc"
    )
    unique_application_number = ArrayField(
        models.TextField(), null=True, blank=True, db_column="unique_application_number"
    )
    utla_name = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="utla_name",
        verbose_name="UTLA name",
    )
    # Array of utla_code IDs
    utla_code_id = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        db_column="utla_code",
        verbose_name="UTLA code",
    )
    # The actual ManyToManyField for utla_code
    utla_code = models.ManyToManyField(
        "ontology.UkLocalAuthority",
        related_name="+",
        blank=True,
        db_column="utla_code",
        verbose_name="UTLA code",
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
    will_notify_la_central_case_flag = models.BooleanField(
        null=True,
        blank=True,
        db_column="will_notify_la_central_case_flag",
        verbose_name="Will notify LA central case flag",
    )
    sponsor_withdrawn = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_withdrawn"
    )
    edited_in_app = models.BooleanField(
        null=True, blank=True, db_column="edited_in_app"
    )

    requires_checks_status_recalculation = models.BooleanField(default=False)

    def display_link_data(self, linked_from, linked_as) -> LinkedRecordData:
        if isinstance(linked_from, MvVolunteer):
            sponsor_withdrawn = (
                linked_from.id in self.sponsor_withdrawn
                and linked_from != self.get_active_host()
                if self.sponsor_withdrawn
                else False
            )

            return LinkedRecordData(
                "accommodation-requests:detail-overview",
                self.id,
                self.title,
                "sponsor_withdrawn" if sponsor_withdrawn else None,
                "Withdrawn" if sponsor_withdrawn else None,
            )

        return LinkedRecordData(
            "accommodation-requests:detail-overview",
            self.id,
            self.title,
        )

    class Meta:
        verbose_name = "Accommodation Request"

    def get_all_ltla_names(self) -> list[str] | None:
        if self.ltla_name:
            return list(self.ltla_name)
        return None

    def get_all_utla_names(self) -> list[str] | None:
        if self.utla_name:
            return list(self.utla_name)
        return None

    def get_people(self) -> list[MvPerson]:
        if self.person_id:
            return list(MvPerson.objects.filter(id__in=self.person_id))
        return []

    def get_people_restrict_for_user(self, user: User):
        return MvPerson.objects.get_for_user(user).filter(id__in=self.person_id or [])

    def get_group(self) -> MvGroup | None:
        if self.group_id:
            return MvGroup.objects.filter(id=self.group_id).first()
        return None

    def get_active_host(self) -> MvVolunteer | None:
        if self.active_host_id:
            return MvVolunteer.objects.filter(id=self.active_host_id).first()
        return None

    def get_active_eoi_host(self) -> EoiHost | None:
        if self.active_eoi_host_id:
            return EoiHost.objects.filter(host_id=self.active_eoi_host_id).first()
        return None

    def get_primary_sponsor(self) -> MvVolunteer | None:
        if self.primary_sponsor_id:
            return MvVolunteer.objects.filter(id=self.primary_sponsor_id).first()
        return None

    def get_primary_accommodation(self) -> MvAccommodation | None:
        if self.primary_accommodation_id:
            return MvAccommodation.objects.filter(
                id=self.primary_accommodation_id
            ).first()
        return None

    @property
    def safeguarding_checks(self):
        host_and_sponsors = self.get_host_and_active_sponsors()
        accommodations = self.get_accommodations()
        return self.get_safeguarding_checks(host_and_sponsors, accommodations)

    def safeguarding_checks_restrict_for_user(self, user: User):
        host_and_sponsors = self.get_host_and_active_sponsors_restrict_for_user(user)
        accommodations = self.get_accommodations_restrict_for_user(user)
        return self.get_safeguarding_checks(host_and_sponsors, accommodations)

    def get_safeguarding_checks(
        self,
        host_and_sponsors: QuerySet[MvVolunteer],
        accommodations: QuerySet[MvAccommodation],
    ):
        q = Q(AR__id=self.id, check_type__id=CheckType.Id.GROUP_ARRIVED)
        group = self.get_group()
        if hasattr(group, "checks"):
            q |= Q(
                id__in=group.checks.values_list("id", flat=True),
                check_type__id=CheckType.Id.GROUP_ARRIVED,
            )

        for accommodation in accommodations:
            if hasattr(accommodation, "checks"):
                q |= Q(
                    AR__id=self.id,
                    id__in=accommodation.checks.filter(
                        check_type__id=CheckType.Id.ACCOMM_SUITABLE
                    ).values_list("id", flat=True),
                )
                q |= Q(
                    id__in=accommodation.checks.filter(
                        check_type__id=CheckType.Id.ACCOMM_EXISTS
                    ).values_list("id", flat=True),
                )

        for sponsor in host_and_sponsors:
            if hasattr(sponsor, "checks"):
                q |= Q(
                    id__in=sponsor.checks.values_list("id", flat=True),
                    check_type__id=CheckType.Id.SPONSOR_DBS,
                )

        if not q.children:
            return DevCheckV2.objects.none()

        return DevCheckV2.objects.filter(q).distinct()

    def get_primary_sponsor_restrict_for_user(self, user: User) -> MvVolunteer | None:
        if self.primary_sponsor_id:
            return (
                MvVolunteer.objects.get_for_user(user)
                .filter(id=self.primary_sponsor_id)
                .first()
            )
        return None

    def get_sponsors_restrict_for_user(self, user: User):
        sponsors = self.sponsor_id or []
        if self.primary_sponsor_id and self.primary_sponsor_id not in sponsors:
            sponsors.append(self.primary_sponsor_id)

        return MvVolunteer.objects.get_for_user(user).filter(id__in=sponsors)

    def get_active_sponsors(self) -> QuerySet:
        sponsors = self.sponsor_id or []
        if self.primary_sponsor_id and self.primary_sponsor_id not in sponsors:
            sponsors.append(self.primary_sponsor_id)

        return MvVolunteer.objects.filter(id__in=sponsors).exclude(
            id__in=self.sponsor_withdrawn or []
        )

    def get_active_sponsors_restrict_for_user(self, user: User):
        all_sponsors = self.get_sponsors_restrict_for_user(user)
        return all_sponsors.exclude(id__in=self.sponsor_withdrawn or [])

    def has_any_active_sponsors(self):
        return self.get_active_sponsors().exists()

    def get_host(self) -> MvVolunteer | None:
        return (
            self.get_active_host()
            if self.get_active_host()
            else self.get_primary_sponsor()
        )

    def get_host_restrict_for_user(self, user: User) -> MvVolunteer | None:
        host = self.get_host()
        if host:
            return (
                MvVolunteer.objects.get_for_user(user)
                .filter(
                    id=host.id,
                )
                .first()
            )

        return None

    @staticmethod
    def combine_host_and_sponsors(
        host: MvVolunteer | None, sponsors: QuerySet[MvVolunteer]
    ) -> QuerySet[MvVolunteer]:
        if host:
            return MvVolunteer.objects.filter(
                Q(pk=host.pk) | Q(pk__in=sponsors.values_list("pk", flat=True))
            )
        return sponsors

    def get_host_and_active_sponsors(self) -> QuerySet[MvVolunteer]:
        return self.combine_host_and_sponsors(
            self.get_host(), self.get_active_sponsors()
        )

    def get_host_and_active_sponsors_restrict_for_user(
        self, user: User
    ) -> QuerySet[MvVolunteer]:
        return self.combine_host_and_sponsors(
            self.get_host_restrict_for_user(user),
            self.get_active_sponsors_restrict_for_user(user),
        )

    def get_accommodation_ids(self) -> list[str]:
        accommodations_ids = list(self.accommodation_id or [])

        if self.bridging_accommodation_id:
            accommodations_ids.append(self.bridging_accommodation_id)

        if self.temporary_accommodation_id:
            accommodations_ids.append(self.temporary_accommodation_id)

        if (
            self.primary_accommodation_id
            and self.primary_accommodation_id not in accommodations_ids
        ):
            accommodations_ids.append(self.primary_accommodation_id)

        return accommodations_ids

    def get_accommodations(self) -> QuerySet[MvAccommodation]:
        accommodations_ids = self.get_accommodation_ids()

        return MvAccommodation.objects.filter(id__in=accommodations_ids)

    @cached_property
    def accommodations(self) -> list[MvAccommodation]:
        return list(self.get_accommodations().select_related("postcode").order_by("id"))

    def get_accommodations_restrict_for_user(self, user: User) -> Q(MvAccommodation):
        accommodations_ids = self.get_accommodation_ids()
        return MvAccommodation.objects.get_for_user(user).filter(
            id__in=accommodations_ids
        )

    def get_primary_accommodation_restrict_for_user(
        self, user: User
    ) -> MvAccommodation | None:
        if self.primary_accommodation_id:
            return (
                MvAccommodation.objects.get_for_user(user)
                .filter(id=self.primary_accommodation_id)
                .first()
            )
        return None

    def get_visa_applications_restrict_for_user(self, user: User) -> Q(VisaApplication):
        if self.unique_application_number:
            return VisaApplication.objects.get_for_user(user).filter(
                application_unique_application_number__in=self.unique_application_number
            )
        return VisaApplication.objects.none()

    def get_sponsorship_certification_forms_restrict_for_user(self, user: User) -> Q(
        SponsorshipCertificationForm
    ):
        if self.sponsorship_certification_number_id:
            return SponsorshipCertificationForm.objects.get_for_user(user).filter(
                pk__in=self.sponsorship_certification_number_id
            )

        return SponsorshipCertificationForm.objects.none()

    def get_primary_contact_person(self) -> MvPerson | None:
        """
        The primary contact is the eldest person on the request.
        """
        eldest_first = sorted(self.get_people(), key=get_person_age_sort_key)
        return eldest_first[0] if eldest_first else None

    def is_primary_contact(self, person: MvPerson) -> bool:
        primary = self.get_primary_contact_person()
        return bool(primary and str(primary.id) == str(person.id))

    def _combine_names(self, first_name: str | None, last_name: str | None) -> str:
        if first_name and last_name:
            return f"{first_name} {last_name}"
        return first_name or last_name or "Unknown"

    def _build_title(self) -> str:
        """
        Builds a title for an Accommodation Request based on:
        - primary contact's full name if known
        - a count of other guest(s) if known
        - the first 14 characters of an accommodation's full address if known
        - the postcode if known
        """
        if self.person_id == []:
            title = "Empty group"
        else:
            title = self._combine_names(
                self.primary_contact_first_name, self.primary_contact_last_name
            )

            if self.number_of_people and self.number_of_people > 1:
                others = self.number_of_people - 1
                title += f" and {others} other{'s' if others > 1 else ''}"

        primary_accommodation = self.get_primary_accommodation()
        if primary_accommodation:
            full_address = primary_accommodation.full_address
            postcode_obj = primary_accommodation.get_postcode()
            postcode = postcode_obj.postcode_formatted if postcode_obj else None

            address_part = full_address[:14] if full_address else "unknown address"
            if postcode:
                address_part += f", {postcode}"

            title += f" to {address_part}"
        return title

    def update_primary_contact(self, person: MvPerson | None) -> bool:
        """
        Update the primary contact fields if they differ from the current ones.
        """
        fields = [
            "first_name",
            "last_name",
            "email",
            "email_for_decision",
            "email_after_decision",
            "email_for_questions",
            "phone",
            "can_be_contacted_by_phone",
        ]

        if person is None:
            return False
        modified = False
        for field in fields:
            current = getattr(self, f"primary_contact_{field}")
            new_value = getattr(person, field)
            if current != new_value:
                setattr(self, f"primary_contact_{field}", new_value)
                modified = True

        if modified:
            self.title = self._build_title()
            self.save()
        return modified

    def update_title(self) -> bool:
        """
        Update the title based on current contact and accommodation info.
        """
        new_title = self._build_title()
        if new_title != self.title:
            self.title = new_title
            self.save()
            return True
        return False

    def get_primary_contact_initials(self) -> str:
        initials = ""

        if self.primary_contact_first_name:
            initials += self.primary_contact_first_name[0]

        if self.primary_contact_last_name:
            initials += self.primary_contact_last_name[0]

        return initials.upper()

    def get_pii_safe_record_name(self) -> str:
        return self.get_primary_contact_initials()

    def update_checks_status(self, status: ChecksStatus, author: User | str | None):
        if self.checks_status == status:
            return

        self.checks_status = status
        self.last_modified_at = timezone.now()
        self.last_modified_by = (
            author.get_full_name() if hasattr(author, "get_full_name") else author
        )
        self.save()

    def update_accommodation(
        self, new_accommodation: MvAccommodation | None, author: User | str
    ):
        for current_accommodation in self.accommodation_id:
            self.previous_accommodation.add(current_accommodation)

        self.accommodation_id = [new_accommodation.pk] if new_accommodation else []
        self.primary_accommodation = new_accommodation if new_accommodation else None

        self.postcode = (
            [new_accommodation.get_postcode().postcode]
            if new_accommodation and new_accommodation.get_postcode()
            else []
        )

        self.last_modified_at = timezone.now()
        self.last_modified_by = (
            author.get_full_name() if hasattr(author, "get_full_name") else author
        )
        self.update_title()
        self.save()

    def update_host(self, new_accommodation: MvAccommodation, author: User | str):
        new_host = new_accommodation.get_volunteer()
        if new_host is None:
            # Fallback to the first host if no volunteer is set
            new_host = new_accommodation.hosts.filter(is_principal=True).first()

        if new_host is None:
            # If no host is set, we cannot update the host
            return

        self.active_host = new_host

        # add new host to the sponsor_id array if is_sponsor is true
        if new_host.is_sponsor:
            if not self.sponsor_id:
                self.sponsor_id = [new_host.id]
            else:
                self.sponsor_id.append(new_host.id)

        self.primary_sponsor = new_host

        self.last_modified_at = timezone.now()
        self.last_modified_by = (
            author.get_full_name() if hasattr(author, "get_full_name") else author
        )
        self.save()

    def update_number_of_people(self):
        self.number_of_people = len(self.person_id)

    def split_guests(self, guest_ids: list[str]):
        group = self.get_group()
        if group is not None:
            new_group = self.group.split_group(guest_ids)
        else:
            new_group = None

        new_request = deepcopy(self)
        new_request.id = uuid4()
        new_request.person_id = guest_ids
        new_request.group = new_group
        new_request.update_number_of_people()
        new_request.update_primary_contact(new_request.get_primary_contact_person())
        new_request.update_title()
        new_request.save()

        # Link guests to new ar
        MvPerson.objects.filter(id__in=guest_ids).update(
            accommodation_request=new_request
        )

        for guest in guest_ids:
            self.person_id.remove(guest)

        self.update_number_of_people()
        self.update_primary_contact(self.get_primary_contact_person())
        self.update_title()
        self.save()

        return new_request

    def mark_sponsor_withdrawn(self, sponsor: MvVolunteer, author: User):
        if self.sponsor_withdrawn:
            self.sponsor_withdrawn.append(sponsor.id)
        else:
            self.sponsor_withdrawn = [sponsor.id]
        self.last_modified_at = timezone.now()
        self.last_modified_by = author.get_full_name()
        self.save()

    def unlink_host(self, author: User):
        active_eoi_host = self.get_active_eoi_host()
        if active_eoi_host:
            self.previous_eoi_hosts.add(active_eoi_host)

        self.active_host = None
        self.active_eoi_host = None
        self.is_eoi_host = None

        self.last_modified_at = timezone.now()
        self.last_modified_by = author.get_full_name()
        self.save()

    def contains_minors(self) -> bool:
        if self.min_age:
            return self.min_age < 18

        people = self.get_people()
        return any(
            (person.age if person.age is not None else 18) < 18 for person in people
        )

    @property
    def is_empty_group(self) -> bool:
        return (self.person_id == []) or (
            self.title and "Empty group" in self.title and self.number_of_people == 0
        )

    def determine_checks_status_from_linked_objects(  # noqa: C901
        self, excluded_statuses=CLOSED_STATUSES
    ):
        if self.checks_status in excluded_statuses:
            return self.checks_status

        if self.is_empty_group:
            return self.ChecksStatus.CLOSED_EMPTY

        hosts_and_sponsor_ids = set()
        if self.active_host_id:
            hosts_and_sponsor_ids.add(self.active_host_id)
        elif self.primary_sponsor_id:
            hosts_and_sponsor_ids.add(self.primary_sponsor_id)
        elif self.sponsor_id:
            hosts_and_sponsor_ids.update(self.sponsor_id)
        if self.sponsor_withdrawn:
            hosts_and_sponsor_ids.difference_update(self.sponsor_withdrawn)

        accommodation_ids = set()
        if self.primary_accommodation_id:
            accommodation_ids.add(self.primary_accommodation_id)
        elif self.accommodation_id:
            accommodation_ids.update(self.accommodation_id)

        accommodations = MvAccommodation.objects.filter(id__in=accommodation_ids)

        if any(
            a.accommodation_type
            == MvAccommodation.AccommodationType.TEMPORARY_ACCOMMODATION
            for a in accommodations
        ):
            return self.ChecksStatus.IN_TEMPORARY_ACCOMMODATION

        group = self.get_group()
        all_recorded_checks = list()
        check_status_q = Q(
            check_status__in=[
                DevCheckV2.CheckStatus.FAILED,
                DevCheckV2.CheckStatus.PASSED,
                DevCheckV2.CheckStatus.NO_LONGER_NEEDED,
            ]
        )

        all_recorded_checks.extend(
            DevCheckV2.objects.filter(
                check_status_q,
                AR__id=self.id,
                check_type__id=CheckType.Id.GROUP_ARRIVED,
            ).all()
        )
        if group:
            all_recorded_checks.extend(
                DevCheckV2.objects.filter(
                    check_status_q,
                    id__in=group.checks.values_list("id", flat=True),
                    check_type__id=CheckType.Id.GROUP_ARRIVED,
                ).all()
            )

        if accommodation_ids:
            accom_suitable_q = Q(
                AR__id=self.id,
                accommodation__in=accommodation_ids,
                check_type_id=CheckType.Id.ACCOMM_SUITABLE,
            )
            accom_exists_q = Q(
                accommodation__in=accommodation_ids,
                check_type_id=CheckType.Id.ACCOMM_EXISTS,
            )

            all_recorded_checks.extend(
                DevCheckV2.objects.filter(check_status_q, accom_suitable_q)
                .annotate(accommodation_ids=ArrayAgg("accommodation__id"))
                .all()
            )
            all_recorded_checks.extend(
                DevCheckV2.objects.filter(check_status_q, accom_exists_q)
                .annotate(accommodation_ids=ArrayAgg("accommodation__id"))
                .all()
            )

        if hosts_and_sponsor_ids:
            all_recorded_checks.extend(
                DevCheckV2.objects.filter(
                    check_status_q,
                    sponsor__in=hosts_and_sponsor_ids,
                    check_type__id=CheckType.Id.SPONSOR_DBS,
                )
                .annotate(sponsor_ids=ArrayAgg("sponsor__id"))
                .all()
            )

        if any(
            check.check_status == DevCheckV2.CheckStatus.FAILED
            for check in all_recorded_checks
        ):
            return self.ChecksStatus.SOME_CHECKS_FAILED

        all_checks_passed = True
        all_pre_arrival_checks_passed = True
        all_hosts_passed_enhanced_dbs = True

        passed_or_unneeded_checks = [
            check
            for check in all_recorded_checks
            if check.check_status
            in [DevCheckV2.CheckStatus.PASSED, DevCheckV2.CheckStatus.NO_LONGER_NEEDED]
        ]

        sponsor_ids_with_any_dbs_check = set()
        accomms_with_accom_exists_check_passed = set()
        accomms_with_accom_suitable_check_passed = set()
        sponsor_ids_with_enhanced_dbs_check = set()
        passed_group_arrived_check_exists = False
        for check in passed_or_unneeded_checks:
            try:
                if check.check_type_id == CheckType.Id.GROUP_ARRIVED:
                    passed_group_arrived_check_exists = True
                elif check.check_type_id == CheckType.Id.ACCOMM_EXISTS:
                    accomms_with_accom_exists_check_passed.update(
                        check.accommodation_ids
                    )
                elif check.check_type_id == CheckType.Id.ACCOMM_SUITABLE:
                    accomms_with_accom_suitable_check_passed.update(
                        check.accommodation_ids
                    )
                elif check.check_type_id == CheckType.Id.SPONSOR_DBS:
                    sponsor_ids_with_any_dbs_check.update(check.sponsor_ids)
                    # Enhanced DBS checks were only required from end of April 2023.
                    # So, if a sponsor has a recorded DBS check from before this,
                    # do not require it to be an Enhanced check.
                    if validate_sponsor_dbs_passed_subtype(
                        check.check_subtype
                    ) == DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS or (
                        check.create_at
                        and check.create_at < datetime(2023, 5, 1, tzinfo=tzutc())
                    ):
                        sponsor_ids_with_enhanced_dbs_check.update(check.sponsor_ids)
            except AttributeError as e:
                logger.warning(
                    "DevCheckV2 object %s is missing expected attributes: %s",
                    check.id,
                    e,
                )
                continue

        all_checks_passed &= passed_group_arrived_check_exists

        if sponsor_ids_with_any_dbs_check != hosts_and_sponsor_ids:
            logger.info(
                (
                    "Sponsor DBS check missing on AR: ar_id=%s. "
                    "Sponsors with recorded DBS checks: %s, "
                    "Expected DBS checks for sponsors: %s. "
                ),
                self.id,
                ", ".join(str(x) for x in sponsor_ids_with_any_dbs_check) or "None",
                ", ".join(str(x) for x in hosts_and_sponsor_ids) or "None",
            )
            all_checks_passed = False
            all_pre_arrival_checks_passed = False
            all_hosts_passed_enhanced_dbs = False

        if sponsor_ids_with_enhanced_dbs_check != hosts_and_sponsor_ids:
            logger.info(
                (
                    "Enhanced Sponsor DBS check missing on AR: ar_id=%s. "
                    "Sponsors with recorded enhanced DBS checks: %s, "
                    "Expected enhanced DBS checks for sponsors: %s. "
                ),
                self.id,
                ", ".join(str(x) for x in sponsor_ids_with_enhanced_dbs_check)
                or "None",
                ", ".join(str(x) for x in hosts_and_sponsor_ids) or "None",
            )
            all_hosts_passed_enhanced_dbs = False

        if (
            accomms_with_accom_exists_check_passed != accommodation_ids
            or accomms_with_accom_suitable_check_passed != accommodation_ids
        ):
            logger.info(
                (
                    "Accommodation exists or suitable check missing on AR: ar_id=%s. "
                    "Accoms with recorded exists checks: %s, "
                    "Accoms with recorded suitable checks: %s, "
                    "Expected checks for accommodations: %s."
                ),
                self.id,
                ", ".join(str(x) for x in accomms_with_accom_exists_check_passed)
                or "None",
                ", ".join(str(x) for x in accomms_with_accom_suitable_check_passed)
                or "None",
                ", ".join(str(x) for x in accommodation_ids) or "None",
            )
            all_checks_passed = False
            all_pre_arrival_checks_passed = False

        enhanced_dbs_required = self.contains_minors() or self.is_uam
        enhanced_dbs_check_ok = (
            not enhanced_dbs_required or all_hosts_passed_enhanced_dbs
        )
        has_valid_sponsor_and_accommodation = (
            len(hosts_and_sponsor_ids) > 0 and len(accommodations) > 0
        )

        if (
            all_checks_passed
            and enhanced_dbs_check_ok
            and has_valid_sponsor_and_accommodation
        ):
            return self.ChecksStatus.CHECKS_COMPLETED

        if (
            all_pre_arrival_checks_passed
            and enhanced_dbs_check_ok
            and has_valid_sponsor_and_accommodation
        ):
            return self.ChecksStatus.PRE_ARRIVAL_CHECKS_COMPLETE

        if any(
            check.check_status == DevCheckV2.CheckStatus.PASSED
            for check in all_recorded_checks
        ):
            logger.info(
                (
                    "AR determined as having Checks Partially Completed: ar_id=%s. "
                    "All checks passed: %s, "
                    "Pre-arrival checks passed: %s, "
                    "Enhanced DBS check ok: %s, "
                    "Has valid sponsor and accommodation: %s."
                ),
                self.id,
                all_checks_passed,
                all_pre_arrival_checks_passed,
                enhanced_dbs_check_ok,
                has_valid_sponsor_and_accommodation,
            )
            return self.ChecksStatus.CHECKS_PARTIALLY_COMPLETED

        return self.ChecksStatus.CHECKS_REQUIRED

    def reset_and_redetermine_status(
        self, author: str, unset_recalculation_flag: bool = False
    ):
        # reset checks status to force re-evaluation, in case of closed AR status
        self.checks_status = MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED

        # re-evaluate checks status from linked objects
        self.checks_status = self.determine_checks_status_from_linked_objects()

        # update ar
        self.last_modified_at = timezone.now()
        self.last_modified_by = author

        if unset_recalculation_flag:
            self.requires_checks_status_recalculation = False

        self.save()

    @property
    def ltla_group_info(self) -> QuerySet[GroupInfo] | None:
        if not self.ltla_name:
            return None

        return GroupInfo.objects.filter(ltla_name__in=self.ltla_name)

    @property
    def utla_group_info(self) -> QuerySet[GroupInfo] | None:
        if not self.utla_name:
            return None

        return GroupInfo.objects.filter(utla_name__in=self.utla_name)

    def __str__(self):
        return self.title or super().__str__()

    def save(self, *args, **kwargs):
        self.edited_in_app = True
        super(MvAccommodationRequest, self).save(*args, **kwargs)
