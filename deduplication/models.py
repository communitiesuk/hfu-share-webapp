import uuid
from datetime import date
from functools import reduce
from typing import Any, Dict

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import ManyToManyField, Q
from django.utils import timezone
from django.utils.formats import date_format

from accounts.models import User
from deduplication.exceptions import DeduplicationException
from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models import (
    MvAccommodation,
    MvAccommodationRequest,
    MvInteraction,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
)
from webapp.enhanced_sentry_logging import (
    db_values,
    exists_when_logging,
    in_memory_values,
    log_event,
    log_persistence_check,
    record_operation_outcome,
)

# Fields (un)linked during deduplication, snapshotted and
# persistence-checked by the dedup logging.
SPONSOR_AR_FIELDS = ("sponsor_id", "primary_sponsor_id", "active_host_id")
ACCOMMODATION_AR_FIELDS = ("primary_accommodation_id", "accommodation_id")


def check_user_is_not_none(user: User):
    if user is None:
        raise DeduplicationException(
            "A user must be provided to perform the deduplication operation."
        )


def handle_deduplication_exceptions(user: User, principal_record, constituent_records):
    check_user_is_not_none(user)

    if principal_record:
        raise DeduplicationException(
            "Cannot perform deduplication on an already deduplicated group"
        )

    if constituent_records.count() < 2:
        raise DeduplicationException(
            "Require at least two constituents to perform deduplication"
        )

    if not all(
        [
            constituent_record.is_principal
            for constituent_record in constituent_records.all()
        ]
    ):
        raise DeduplicationException("Cannot deduplicate using non principal records")


def calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def log_dedup_event(message: str, *, level: str = "info", **attributes: Any) -> None:
    if not getattr(settings, "ENHANCED_DEDUPLICATION_LOGGING", False):
        return
    log_event(message, level=level, **attributes)


def log_dedup_persistence_check(
    message: str,
    *,
    changes: dict[str, tuple[Any, Any]],
    before: dict[str, Any] | None = None,
    **attributes: Any,
) -> None:
    if not getattr(settings, "ENHANCED_DEDUPLICATION_LOGGING", False):
        return
    log_persistence_check(message, changes=changes, before=before, **attributes)


def _db_values(instance: models.Model, *fields: str) -> dict[str, Any]:
    if not getattr(settings, "ENHANCED_DEDUPLICATION_LOGGING", False):
        return {}
    return db_values(instance, *fields)


def _in_memory_values(instance: models.Model, *fields: str) -> dict[str, Any]:
    if not getattr(settings, "ENHANCED_DEDUPLICATION_LOGGING", False):
        return {}
    return in_memory_values(instance, *fields)


def _exists_when_logging(queryset: models.QuerySet) -> bool | None:
    if not getattr(settings, "ENHANCED_DEDUPLICATION_LOGGING", False):
        return None
    return exists_when_logging(queryset)


class SponsorDuplicateGroupManager(
    LocalAuthorityPermissionsManagerMixin, models.Manager
):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        sponsors_cannot_view = MvVolunteer.objects.exclude(
            MvVolunteer.objects._filter_by_ltla_name(ltla_names)
        )
        return ~Q(sponsors__in=sponsors_cannot_view) & ~Q(
            principal_record__in=sponsors_cannot_view
        )

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        sponsors_cannot_view = MvVolunteer.objects.exclude(
            MvVolunteer.objects._filter_by_utla_name(utla_names)
        )
        return ~Q(sponsors__in=sponsors_cannot_view) & ~Q(
            principal_record__in=sponsors_cannot_view
        )

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        sponsors_cannot_view = MvVolunteer.objects.exclude(
            MvVolunteer.objects._filter_by_viewer_group_name(viewer_group_names)
        )
        return ~Q(sponsors__in=sponsors_cannot_view) & ~Q(
            principal_record__in=sponsors_cannot_view
        )


class SponsorDuplicateGroup(models.Model):
    objects = SponsorDuplicateGroupManager()

    principal_record = models.ForeignKey(
        "ontology.MvVolunteer",
        on_delete=models.SET_NULL,
        null=True,
        db_column="principal_record_id",
    )
    sponsors = ManyToManyField(
        "ontology.MvVolunteer",
        db_table="ontology_sponsor_to_duplicate_group",
        related_name="duplicate_group",
    )
    created_at = models.DateTimeField(default=timezone.now)
    source_sponsor_ar_mapping = ArrayField(models.JSONField(), default=list)
    archived_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(null=False, default=False)

    def _format_sponsor_names(self, sponsors):
        names = [str(s.full_name) for s in sponsors]
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        names.sort()
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return f"{', '.join(names[:-1])} and {names[-1]}"

    @record_operation_outcome("sponsor")
    @transaction.atomic
    def deduplicate(self, principal_record_values: dict[str, Any], user: User):  # noqa: C901
        handle_deduplication_exceptions(user, self.principal_record, self.sponsors)

        sponsors: list[MvVolunteer] = list(self.sponsors.all())

        log_dedup_event(
            "SponsorDuplicateGroup.deduplicate: started",
            group_id=self.pk,
            user=user.pk,
            duplicate_record_count=len(sponsors),
            duplicate_record_pks=[s.pk for s in sponsors],
        )

        principal_record_values["is_principal"] = True
        principal_record_values["is_editable"] = True
        principal_record_values["notional_data"] = any(
            sponsor.notional_data for sponsor in sponsors
        )
        principal_record_values["adverse_hit"] = any(
            sponsor.adverse_hit for sponsor in sponsors
        )
        principal_record_values["source"] = list(
            reduce(
                lambda sources, sponsor: sources + list(sponsor.source or []),
                sponsors,
                [],
            )
        )
        principal_record_values["viewer_group_names"] = list(
            reduce(
                lambda viewer_group_names, sponsor: viewer_group_names
                + list(sponsor.viewer_group_names or []),
                sponsors,
                [],
            )
        )
        principal_record_values["gwf"] = list(
            reduce(
                lambda gwfs, sponsor: gwfs + list(sponsor.gwf or []),
                sponsors,
                [],
            )
        )
        principal_record_values["response_id"] = list(
            reduce(
                lambda response_ids, sponsor: response_ids
                + list(sponsor.response_id or []),
                sponsors,
                [],
            )
        )
        principal_record_values["requested_checks_latest_date"] = max(
            (
                sponsor.requested_checks_latest_date
                for sponsor in sponsors
                if sponsor.requested_checks_latest_date
            ),
            default=None,
        )
        principal_record_values["is_eoi"] = any(sponsor.is_eoi for sponsor in sponsors)
        principal_record_values["is_sponsor"] = any(
            sponsor.is_sponsor for sponsor in sponsors
        )
        principal_record_values["created_date"] = min(
            (sponsor.created_date for sponsor in sponsors if sponsor.created_date),
            default=None,
        )
        principal_record_values["last_updated_date"] = max(
            (
                sponsor.last_updated_date
                for sponsor in sponsors
                if sponsor.last_updated_date
            ),
            default=None,
        )
        principal_record_values["sponsor_type"] = MvVolunteer.SponsorType.INDIVIDUAL

        if "date_of_birth" in principal_record_values:
            principal_record_values["age"] = calculate_age(
                principal_record_values["date_of_birth"]
            )

        new_principal = MvVolunteer.objects.create(
            **principal_record_values,
        )

        # save to get a pk
        new_principal.save()

        log_dedup_persistence_check(
            "SponsorDuplicateGroup.deduplicate: new principal created",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            changes={
                "new_principal_id": (
                    new_principal.pk,
                    _db_values(new_principal, "id").get("id"),
                ),
            },
        )

        # Handle linked records
        self._handle_linked_accommodations(new_principal, sponsors)
        self._handle_linked_accommodation_requests(new_principal, sponsors, user)
        self._handle_linked_safeguarding_checks(new_principal, sponsors)
        self._handle_linked_visa_applications(new_principal, sponsors)
        self._handle_linked_sponsorship_certification_forms(new_principal, sponsors)

        for sponsor in sponsors:
            sponsor.is_principal = False
            sponsor.save()
            log_dedup_persistence_check(
                "SponsorDuplicateGroup.deduplicate: duplicate record merged",
                group_id=self.pk,
                duplicate_record_pk=sponsor.pk,
                new_principal_pk=new_principal.pk,
                changes={
                    "is_principal": (
                        sponsor.is_principal,
                        _db_values(sponsor, "is_principal").get("is_principal"),
                    ),
                },
            )

        self.principal_record = new_principal
        self.principal_record.save()
        self.save()

        log_dedup_persistence_check(
            "SponsorDuplicateGroup.deduplicate: finished",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            changes={
                "principal_record_id": (
                    self.principal_record_id,
                    _db_values(self, "principal_record_id").get("principal_record_id"),
                ),
            },
        )

        # Add interactions for deduplication event
        for record in sponsors:
            others = [s for s in sponsors if s != record]
            if len(others) == 1:
                other_name = others[0].full_name
                note = (
                    f"This record, and sponsor and host record {other_name}"
                    f" were marked as duplicates. "
                    f"New principal record is {new_principal.full_name}."
                )
            else:
                other_names = self._format_sponsor_names(others)
                note = (
                    f"This record, and sponsor and host records {other_names}"
                    f" were marked as duplicates. "
                    f"New principal record is {new_principal.full_name}."
                )
            MvInteraction.objects.create(
                interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                created_by=user,
                title="Record deduplicated",
                interaction_notes=note,
                linked_sponsor=record,
            )

        MvInteraction.objects.create(
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
            interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
            created_by=user,
            title="Record deduplicated",
            interaction_notes=(
                f"This record was created after sponsor and host records "
                f"{self._format_sponsor_names(sponsors)} "
                f"were marked as duplicates."
            ),
            linked_sponsor=new_principal,
        )

    @record_operation_outcome("sponsor")
    @transaction.atomic
    def undo_deduplication(self, user: User):  # noqa: C901
        check_user_is_not_none(user)

        sponsors: list[MvVolunteer] = list(self.sponsors.all())

        log_dedup_event(
            "SponsorDuplicateGroup.undo_deduplication: started",
            group_id=self.pk,
            user=user.pk,
            principal_record_id=self.principal_record_id,
            restored_record_pks=[s.pk for s in sponsors],
            source_sponsor_ar_mapping=self.source_sponsor_ar_mapping,
        )

        for sponsor in sponsors:
            sponsor.is_principal = True
            sponsor.save()

            # Remove principal from safeguarding checks
            for check in sponsor.checks.all():  # type: DevCheckV2
                check.sponsor.remove(self.principal_record)

            # Links the accommodation of sponsors back to the original sponsor
            # removing the principal
            for accommodation in sponsor.accommodations.all():
                before_volunteer_id = accommodation.volunteer_id
                accommodation.volunteer = sponsor
                accommodation.save()
                log_dedup_persistence_check(
                    "SponsorDuplicateGroup.undo_deduplication: "
                    "accommodation moved back",
                    group_id=self.pk,
                    accommodation_pk=accommodation.pk,
                    sponsor_pk=sponsor.pk,
                    volunteer_id_before=before_volunteer_id,
                    changes={
                        "volunteer_id": (
                            accommodation.volunteer_id,
                            _db_values(accommodation, "volunteer_id").get(
                                "volunteer_id"
                            ),
                        ),
                    },
                )

        # Links ARs back to relevant sponsor
        for ar in self.principal_record.get_accommodation_requests():
            for original_ar in self.source_sponsor_ar_mapping:
                if ar.pk == original_ar["ar_pk"]:
                    before = _in_memory_values(ar, *SPONSOR_AR_FIELDS)

                    ar.sponsor_id = ar.sponsor_id or []

                    if self.principal_record_id in ar.sponsor_id:
                        ar.sponsor_id.remove(self.principal_record.pk)

                    if original_ar["sponsor_pk"] not in ar.sponsor_id:
                        ar.sponsor_id.insert(0, original_ar["sponsor_pk"])

                    sponsor = next(
                        s
                        for s in self.sponsors.all()
                        if s.pk == original_ar["sponsor_pk"]
                    )

                    if ar.primary_sponsor == self.principal_record:
                        ar.primary_sponsor = sponsor

                    if ar.active_host == self.principal_record:
                        ar.active_host = sponsor

                    ar.checks_status = ar.determine_checks_status_from_linked_objects()
                    ar.last_modified_at = timezone.now()
                    ar.last_modified_by = user.get_full_name()

                    ar.save()

                    persisted = _db_values(ar, *SPONSOR_AR_FIELDS)
                    log_dedup_persistence_check(
                        "SponsorDuplicateGroup.undo_deduplication: AR moved back",
                        group_id=self.pk,
                        ar_pk=ar.pk,
                        target_sponsor_pk=original_ar["sponsor_pk"],
                        principal_record_id=self.principal_record_id,
                        before=before,
                        changes={
                            field: (getattr(ar, field), persisted.get(field))
                            for field in SPONSOR_AR_FIELDS
                        },
                    )

        # Archives old principal record
        self.principal_record.is_principal = False
        self.principal_record.is_archived = True
        archived_time = timezone.now()
        self.principal_record.archived_at = archived_time
        self.principal_record.save()
        self.is_archived = True
        self.archived_at = archived_time
        self.save()

        log_dedup_persistence_check(
            "SponsorDuplicateGroup.undo_deduplication: finished",
            group_id=self.pk,
            changes={},
        )

        # Add interactions for undo deduplication event
        for record in sponsors:
            others = [s for s in sponsors if s != record]
            if len(others) == 1:
                other_name = others[0].full_name
                note = (
                    f"This record, and sponsor and host record {other_name} "
                    f"were restored as separate principal records. "
                    f"A principal record combining data from both was deleted."
                )
            else:
                other_names = self._format_sponsor_names(others)
                note = (
                    f"This record, and sponsor and host record {other_names} "
                    f"were restored as separate principal records. "
                    f"A principal record combining data from both was deleted."
                )
            MvInteraction.objects.create(
                interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
                interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
                created_by=user,
                title="Deduplication undone",
                interaction_notes=note,
                linked_sponsor=record,
            )

    def has_blocking_multi_la_accommodation_request(self, sponsor: MvVolunteer) -> bool:
        ars = sponsor.get_accommodation_requests()
        unique_ltla_names = {ltla_name for ar in ars for ltla_name in ar.ltla_name}
        return len(unique_ltla_names) > 1

    def can_undo_deduplication(self, sponsor: MvVolunteer) -> bool:
        return not self.has_blocking_multi_la_accommodation_request(sponsor)

    def _handle_linked_safeguarding_checks(
        self, new_principal: MvVolunteer, sponsors: list[MvVolunteer]
    ):
        """
        Links the devcheckv2s of sponsors to the new principal,
        old sponsors remain linked as before
        """
        log_dedup_event(
            "SponsorDuplicateGroup._handle_linked_safeguarding_checks: started",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            sponsor_pks=[s.pk for s in sponsors],
        )
        for sponsor in sponsors:
            for check in sponsor.checks.all():  # type: DevCheckV2
                check.sponsor.add(new_principal)
                log_dedup_persistence_check(
                    "SponsorDuplicateGroup._handle_linked_safeguarding_checks: "
                    "check linked",
                    group_id=self.pk,
                    new_principal_pk=new_principal.pk,
                    sponsor_pk=sponsor.pk,
                    check_pk=check.pk,
                    changes={
                        "new_principal_linked_to_check": (
                            True,
                            _exists_when_logging(
                                check.sponsor.filter(pk=new_principal.pk)
                            ),
                        ),
                    },
                )

    def _handle_linked_accommodation_requests(
        self, new_principal: MvVolunteer, sponsors: list[MvVolunteer], user: User
    ):
        """
        Links the accommodation requests of sponsors to the new principal, stores links
        to old sponsors on the duplicate group to allow for undo deduplication
        """
        log_dedup_event(
            "SponsorDuplicateGroup._handle_linked_accommodation_requests: started",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            sponsor_pks=[s.pk for s in sponsors],
        )
        for sponsor in sponsors:
            for ar in sponsor.get_accommodation_requests():
                self.source_sponsor_ar_mapping.append(
                    {
                        "ar_pk": ar.pk,
                        "sponsor_pk": sponsor.pk,
                    }
                )
                self.save()

                before = _in_memory_values(ar, *SPONSOR_AR_FIELDS)

                ar.sponsor_id = ar.sponsor_id or []

                if sponsor.pk in ar.sponsor_id:
                    ar.sponsor_id.remove(sponsor.pk)

                if new_principal.pk not in ar.sponsor_id:
                    ar.sponsor_id.insert(0, new_principal.pk)

                if sponsor == ar.primary_sponsor:
                    ar.primary_sponsor = new_principal

                if sponsor == ar.active_host:
                    ar.active_host = new_principal

                ar.checks_status = ar.determine_checks_status_from_linked_objects()
                ar.last_modified_at = timezone.now()
                ar.last_modified_by = user.get_full_name()

                ar.save()

                persisted = _db_values(ar, *SPONSOR_AR_FIELDS)
                log_dedup_persistence_check(
                    "SponsorDuplicateGroup._handle_linked_accommodation_requests: "
                    "AR linked",
                    group_id=self.pk,
                    ar_pk=ar.pk,
                    sponsor_pk=sponsor.pk,
                    new_principal_pk=new_principal.pk,
                    before=before,
                    changes={
                        field: (getattr(ar, field), persisted.get(field))
                        for field in SPONSOR_AR_FIELDS
                    },
                )

    def _handle_linked_accommodations(
        self, new_principal: MvVolunteer, sponsors: list[MvVolunteer]
    ):
        """
        Links the accommodation of sponsors to the new principal,
        old sponsors remain linked via the hosts field on accommodation
        """
        log_dedup_event(
            "SponsorDuplicateGroup._handle_linked_accommodations: started",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            sponsor_pks=[s.pk for s in sponsors],
        )
        for sponsor in sponsors:
            for accommodation in sponsor.accommodations.all():
                before_volunteer_id = accommodation.volunteer_id
                accommodation.volunteer = new_principal

                # This is equivalent to adding the sponsor to the hosts field of
                # the accommodation
                new_principal.accommodations.add(accommodation)
                accommodation.save()

                log_dedup_persistence_check(
                    "SponsorDuplicateGroup._handle_linked_accommodations: "
                    "accommodation linked",
                    group_id=self.pk,
                    accommodation_pk=accommodation.pk,
                    sponsor_pk=sponsor.pk,
                    new_principal_pk=new_principal.pk,
                    volunteer_id_before=before_volunteer_id,
                    changes={
                        "volunteer_id": (
                            accommodation.volunteer_id,
                            _db_values(accommodation, "volunteer_id").get(
                                "volunteer_id"
                            ),
                        ),
                    },
                )

    def _handle_linked_sponsorship_certification_forms(
        self, new_principal: MvVolunteer, sponsors: list[MvVolunteer]
    ):
        """
        Links the sponsorship certification forms of sponsors to the new principal,
        without breaking old links
        """
        new_principal.sponsorship_certification_number_id = list(
            reduce(
                lambda cert_numbers, sponsor: cert_numbers
                + list(sponsor.sponsorship_certification_number_id or []),
                sponsors,
                [],
            )
        )

        log_dedup_event(
            "SponsorDuplicateGroup._handle_linked_sponsorship_certification_forms: "
            "cert forms set",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            cert_numbers_in_memory=(new_principal.sponsorship_certification_number_id),
            cert_numbers_persisted=_db_values(
                new_principal, "sponsorship_certification_number_id"
            ).get("sponsorship_certification_number_id"),
            note=(
                "Set on new_principal in memory only. Not saved here; "
                "persisted by the later principal_record.save() in "
                "deduplicate(), so in-memory and DB values differ now by "
                "design."
            ),
        )

    def _handle_linked_visa_applications(
        self, new_principal: MvVolunteer, sponsors: list[MvVolunteer]
    ):
        """
        Links the visa applications of sponsors to the new principal,
        without breaking old links
        """
        new_principal.application_unique_application_number = list(
            reduce(
                lambda application_numbers, sponsor: application_numbers
                + list(sponsor.application_unique_application_number or []),
                sponsors,
                [],
            )
        )

        log_dedup_event(
            "SponsorDuplicateGroup._handle_linked_visa_applications: "
            "visa applications set",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            visa_application_numbers_in_memory=(
                new_principal.application_unique_application_number
            ),
            visa_application_numbers_persisted=_db_values(
                new_principal, "application_unique_application_number"
            ).get("application_unique_application_number"),
            note=(
                "Set on new_principal in memory only. Not saved here; "
                "persisted by the later principal_record.save() in "
                "deduplicate(), so in-memory and DB values differ now by "
                "design."
            ),
        )


class AccommodationDuplicateGroupManager(
    LocalAuthorityPermissionsManagerMixin, models.Manager
):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        accommodations_cannot_view = MvAccommodation.objects.exclude(
            MvAccommodation.objects._filter_by_ltla_name(ltla_names)
        )
        return ~Q(accommodations__in=accommodations_cannot_view) & ~Q(
            principal_record__in=accommodations_cannot_view
        )

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        accommodations_cannot_view = MvAccommodation.objects.exclude(
            MvAccommodation.objects._filter_by_utla_name(utla_names)
        )
        return ~Q(accommodations__in=accommodations_cannot_view) & ~Q(
            principal_record__in=accommodations_cannot_view
        )

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        accommodations_cannot_view = MvAccommodation.objects.exclude(
            MvAccommodation.objects._filter_by_viewer_group_name(viewer_group_names)
        )
        return ~Q(accommodations__in=accommodations_cannot_view) & ~Q(
            principal_record__in=accommodations_cannot_view
        )


class AccommodationDuplicateGroup(models.Model):
    objects = AccommodationDuplicateGroupManager()

    principal_record = models.ForeignKey(
        "ontology.MvAccommodation",
        on_delete=models.SET_NULL,
        null=True,
        db_column="principal_record_id",
    )
    accommodations = ManyToManyField(
        "ontology.MvAccommodation",
        db_table="ontology_accommodation_to_duplicate_group",
        related_name="duplicate_group",
    )
    created_at = models.DateTimeField(default=timezone.now)
    source_accommodation_ar_mapping = ArrayField(models.JSONField(), default=list)
    archived_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(null=False, default=False)

    def _format_accommodation_addresses(self, accommodations):
        addresses = [str(s.full_address) for s in accommodations]
        if not addresses:
            return ""
        if len(addresses) == 1:
            return addresses[0]
        addresses.sort()
        if len(addresses) == 2:
            return f"{addresses[0]} and {addresses[1]}"
        return f"{', '.join(addresses[:-1])} and {addresses[-1]}"

    def _value_or_list(self, values):
        if not values:
            return None
        if len(values) == 1:
            return next(iter(values))
        return list(values)

    @record_operation_outcome("accommodation")
    @transaction.atomic
    def deduplicate(self, principal_record_values: dict[str, Any], user: User):  # noqa: C901
        handle_deduplication_exceptions(
            user, self.principal_record, self.accommodations
        )

        accommodations: list[MvAccommodation] = list(self.accommodations.all())

        log_dedup_event(
            "AccommodationDuplicateGroup.deduplicate: started",
            group_id=self.pk,
            user=user.pk,
            duplicate_record_count=len(accommodations),
            duplicate_record_pks=[a.pk for a in accommodations],
        )

        accommodation_availabilities = {
            accommodation.accommodation_availability
            for accommodation in accommodations
            if accommodation.accommodation_availability
        }
        if accommodation_availabilities:
            principal_record_values["accommodation_availability"] = self._value_or_list(
                accommodation_availabilities
            )
        accommodation_providers = {
            accommodation.accommodation_provider
            for accommodation in accommodations
            if accommodation.accommodation_provider
        }
        if accommodation_providers:
            principal_record_values["accommodation_provider"] = self._value_or_list(
                accommodation_providers
            )
        accommodation_provider_types = {
            accommodation.accommodation_provider_type
            for accommodation in accommodations
            if accommodation.accommodation_provider_type
        }
        if accommodation_provider_types:
            principal_record_values["accommodation_provider_type"] = (
                self._value_or_list(accommodation_provider_types)
            )
        accommodation_types = {
            accommodation.accommodation_type
            for accommodation in accommodations
            if accommodation.accommodation_type
        }
        if len(accommodation_types) == 1:
            principal_record_values["accommodation_type"] = accommodation_types.pop()

        principal_record_values["allow_pet"] = any(
            accommodation.allow_pet for accommodation in accommodations
        )
        principal_record_values["application_unique_application_number"] = list(
            set(
                reduce(
                    lambda ids, accommodation: ids
                    + list(accommodation.application_unique_application_number or []),
                    accommodations,
                    [],
                )
            )
        )
        countries = {
            accommodation.country
            for accommodation in accommodations
            if accommodation.country
        }
        if countries:
            principal_record_values["country"] = self._value_or_list(countries)
        principal_record_values["created_at"] = min(
            (
                accommodation.created_at
                for accommodation in accommodations
                if accommodation.created_at
            ),
            default=None,
        )
        principal_record_values["created_by"] = user.email
        principal_record_values["created_date"] = min(
            (
                accommodation.created_date
                for accommodation in accommodations
                if accommodation.created_date
            ),
            default=None,
        )
        principal_record_values["gwf"] = list(
            set(
                reduce(
                    lambda gwfs, accommodation: gwfs + list(accommodation.gwf or []),
                    accommodations,
                    [],
                )
            )
        )
        principal_record_values["is_accommodation"] = any(
            accommodation.is_accommodation for accommodation in accommodations
        )
        principal_record_values["is_editable"] = True
        principal_record_values["is_eoi"] = any(
            accommodation.is_eoi for accommodation in accommodations
        )
        principal_record_values["is_principal"] = True
        principal_record_values["is_residential"] = any(
            accommodation.is_residential for accommodation in accommodations
        )
        principal_record_values["last_modified_date"] = max(
            (
                accommodation.last_modified_date
                for accommodation in accommodations
                if accommodation.last_modified_date
            ),
            default=None,
        )
        if "ltla_name" in principal_record_values:
            principal_record_values["local_authority"] = principal_record_values[
                "ltla_name"
            ]
        principal_record_values["notional_data"] = any(
            accommodation.notional_data for accommodation in accommodations
        )
        number_adults_set = {
            accommodation.number_adults
            for accommodation in accommodations
            if accommodation.number_adults is not None
        }
        if len(number_adults_set) == 1:
            principal_record_values["number_adults"] = number_adults_set.pop()
        number_children_set = {
            accommodation.number_children
            for accommodation in accommodations
            if accommodation.number_children is not None
        }
        if len(number_children_set) == 1:
            principal_record_values["number_children"] = number_children_set.pop()
        number_of_double_rooms_available_set = {
            accommodation.number_of_double_rooms_available
            for accommodation in accommodations
            if accommodation.number_of_double_rooms_available is not None
        }
        if len(number_of_double_rooms_available_set) == 1:
            principal_record_values["number_of_double_rooms_available"] = (
                number_of_double_rooms_available_set.pop()
            )
        number_of_single_rooms_set = {
            accommodation.number_of_single_rooms
            for accommodation in accommodations
            if accommodation.number_of_single_rooms is not None
        }
        if len(number_of_single_rooms_set) == 1:
            principal_record_values["number_of_single_rooms"] = (
                number_of_single_rooms_set.pop()
            )
        principal_record_values["response_id"] = list(
            set(
                reduce(
                    lambda response_ids, accommodation: response_ids
                    + list(accommodation.response_id or []),
                    accommodations,
                    [],
                )
            )
        )
        principal_record_values["requested_checks_latest_date"] = max(
            (
                accommodation.requested_checks_latest_date
                for accommodation in accommodations
                if accommodation.requested_checks_latest_date
            ),
            default=None,
        )
        principal_record_values["source"] = list(
            set(
                reduce(
                    lambda sources, accommodation: sources
                    + list(accommodation.source or []),
                    accommodations,
                    [],
                )
            )
        )
        principal_record_values["sponsorship_certification_number_id"] = list(
            set(
                reduce(
                    lambda ids, accommodation: ids
                    + list(accommodation.sponsorship_certification_number_id or []),
                    accommodations,
                    [],
                )
            )
        )
        principal_record_values["submission_guids"] = list(
            {
                guid
                for accommodation in accommodations
                for guid in (
                    (
                        [accommodation.submission_guid]
                        if accommodation.submission_guid
                        else []
                    )
                    + (
                        list(accommodation.submission_guids)
                        if accommodation.submission_guids
                        else []
                    )
                )
            }
        )
        principal_record_values["viewer_group_names"] = list(
            reduce(
                lambda viewer_group_names, accommodation: viewer_group_names
                + list(accommodation.viewer_group_names or []),
                accommodations,
                [],
            )
        )
        volunteers = []
        for accommodation in accommodations:
            volunteer = accommodation.get_volunteer()
            if isinstance(volunteer, MvVolunteer):
                volunteers.append(volunteer)
        principal_record_values["volunteer"] = volunteers[0] if volunteers else None
        principal_record_values["what_type_of_living_space_can_you_offer"] = list(
            set(
                reduce(
                    lambda living_space, accommodation: living_space
                    + (
                        accommodation.what_type_of_living_space_can_you_offer
                        if accommodation.what_type_of_living_space_can_you_offer
                        else []
                    ),
                    accommodations,
                    [],
                )
            )
        )
        principal_record_values["wheelchair_accessible"] = any(
            accommodation.wheelchair_accessible for accommodation in accommodations
        )
        who_can_you_accommodate_answers = {
            accommodation.who_can_you_accommodate
            for accommodation in accommodations
            if accommodation.who_can_you_accommodate
        }
        if who_can_you_accommodate_answers:
            principal_record_values["who_can_you_accommodate"] = self._value_or_list(
                who_can_you_accommodate_answers
            )
        principal_record_values["edited_in_app"] = True

        new_principal = MvAccommodation.objects.create(
            id=f"accommodation-{uuid.uuid4()}",
            **principal_record_values,
        )

        # save to get a pk
        new_principal.save()
        new_principal.hosts.set(
            [
                host
                for accommodation in accommodations
                for host in accommodation.hosts.all()
            ]
        )

        log_dedup_persistence_check(
            "AccommodationDuplicateGroup.deduplicate: new principal created",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            changes={
                "new_principal_id": (
                    new_principal.pk,
                    _db_values(new_principal, "id").get("id"),
                ),
            },
        )

        # Handle linked records
        self._handle_linked_accommodation_requests(new_principal, accommodations, user)

        for accommodation in accommodations:
            accommodation.is_principal = False
            accommodation.save()
            log_dedup_persistence_check(
                "AccommodationDuplicateGroup.deduplicate: duplicate record merged",
                group_id=self.pk,
                duplicate_record_pk=accommodation.pk,
                new_principal_pk=new_principal.pk,
                changes={
                    "is_principal": (
                        accommodation.is_principal,
                        _db_values(accommodation, "is_principal").get("is_principal"),
                    ),
                },
            )

        self.principal_record = new_principal
        self.principal_record.save()
        self.save()

        log_dedup_persistence_check(
            "AccommodationDuplicateGroup.deduplicate: finished",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            changes={
                "principal_record_id": (
                    self.principal_record_id,
                    _db_values(self, "principal_record_id").get("principal_record_id"),
                ),
            },
        )

        # Add interactions for deduplication event
        for record in accommodations:
            others = [s for s in accommodations if s != record]
            if len(others) == 1:
                other_accommodation = others[0].full_address
                note = (
                    f"This record, and accommodation record "
                    f"{other_accommodation} were marked as duplicates. "
                    f"New principal record is {new_principal.full_address}."
                )
            else:
                other_accommodations = self._format_accommodation_addresses(others)
                note = (
                    f"This record, and accommodation records "
                    f"{other_accommodations} were marked as duplicates. "
                    f"New principal record is {new_principal.full_address}."
                )
            MvInteraction.objects.create(
                interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                created_by=user,
                title="Record deduplicated",
                interaction_notes=note,
                linked_accommodation=record,
            )

        MvInteraction.objects.create(
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
            interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
            created_by=user,
            title="Record deduplicated",
            interaction_notes=(
                f"This record was created after accommodation records "
                f"{self._format_accommodation_addresses(accommodations)} "
                f"were marked as duplicates."
            ),
            linked_accommodation=new_principal,
        )

    @record_operation_outcome("accommodation")
    @transaction.atomic
    def undo_deduplication(self, user: User):  # noqa: C901
        check_user_is_not_none(user)

        accommodations: list[MvAccommodation] = list(self.accommodations.all())

        log_dedup_event(
            "AccommodationDuplicateGroup.undo_deduplication: started",
            group_id=self.pk,
            user=user.pk,
            principal_record_id=self.principal_record_id,
            restored_record_pks=[a.pk for a in accommodations],
            source_accommodation_ar_mapping=self.source_accommodation_ar_mapping,
        )

        for accommodation in accommodations:
            accommodation.is_principal = True
            accommodation.save()

        self.principal_record.hosts.clear()

        # Links ARs back to relevant accommodation
        for ar in self.principal_record.get_accommodation_requests():
            for original_ar in self.source_accommodation_ar_mapping:
                if ar.pk == original_ar["ar_pk"]:
                    before = _in_memory_values(ar, *ACCOMMODATION_AR_FIELDS)

                    # Update primary_accommodation
                    if ar.primary_accommodation_id == self.principal_record_id:
                        ar.primary_accommodation_id = original_ar["accommodation_pk"]

                    # Remove principal record and insert original accommodation
                    if (
                        ar.accommodation_id
                        and self.principal_record_id in ar.accommodation_id
                    ):
                        ar.accommodation_id = [
                            aid
                            for aid in ar.accommodation_id
                            if aid != self.principal_record_id
                        ]
                        ar.accommodation_id.append(original_ar["accommodation_pk"])

                    ar.checks_status = ar.determine_checks_status_from_linked_objects()
                    ar.last_modified_at = timezone.now()
                    ar.last_modified_by = user.get_full_name()
                    ar.save()

                    persisted = _db_values(ar, *ACCOMMODATION_AR_FIELDS)
                    log_dedup_persistence_check(
                        "AccommodationDuplicateGroup.undo_deduplication: AR moved back",
                        group_id=self.pk,
                        ar_pk=ar.pk,
                        target_accommodation_pk=original_ar["accommodation_pk"],
                        principal_record_id=self.principal_record_id,
                        before=before,
                        changes={
                            field: (getattr(ar, field), persisted.get(field))
                            for field in ACCOMMODATION_AR_FIELDS
                        },
                    )

        # Archives old principal record
        self.principal_record.is_principal = False
        self.principal_record.is_archived = True
        archived_time = timezone.now()
        self.principal_record.archived_at = archived_time
        self.principal_record.save()
        self.is_archived = True
        self.archived_at = archived_time
        self.save()

        log_dedup_persistence_check(
            "AccommodationDuplicateGroup.undo_deduplication: finished",
            group_id=self.pk,
            changes={},
        )

        # Add interactions for undo deduplication event
        for record in accommodations:
            others = [s for s in accommodations if s != record]
            if len(others) == 1:
                other_accommodation = others[0].full_address
                note = (
                    f"This record, and accommodation record {other_accommodation} "
                    f"were restored as separate principal records. "
                    f"A principal record combining data from both was deleted."
                )
            else:
                other_accommodations = self._format_accommodation_addresses(others)
                note = (
                    f"This record, and accommodation record {other_accommodations} "
                    f"were restored as separate principal records. "
                    f"A principal record combining data from both was deleted."
                )
            MvInteraction.objects.create(
                interaction_contact=(
                    MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE
                ),
                interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
                created_by=user,
                title="Deduplication undone",
                interaction_notes=note,
                linked_accommodation=record,
            )

    def _handle_linked_accommodation_requests(
        self,
        new_principal: MvAccommodation,
        accommodations: list[MvAccommodation],
        user: User,
    ):
        """
        Links the accommodation requests of accommodations to the new principal, stores
        links to old accommodations on the duplicate group to allow for undo
        deduplication
        """
        log_dedup_event(
            "AccommodationDuplicateGroup._handle_linked_accommodation_requests: "
            "started",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            accommodation_pks=[a.pk for a in accommodations],
        )
        for accommodation in accommodations:
            for ar in accommodation.get_accommodation_requests():
                self.source_accommodation_ar_mapping.append(
                    {
                        "ar_pk": ar.pk,
                        "accommodation_pk": accommodation.pk,
                    }
                )
                self.save()

                before = _in_memory_values(ar, *ACCOMMODATION_AR_FIELDS)

                # Replace the primary accommodation
                ar.primary_accommodation = new_principal

                # Update the accommodation_id ArrayField
                if accommodation.pk in ar.accommodation_id:
                    ar.accommodation_id.remove(accommodation.pk)
                if new_principal.pk not in ar.accommodation_id:
                    ar.accommodation_id.insert(0, new_principal.pk)

                ar.checks_status = ar.determine_checks_status_from_linked_objects()
                ar.last_modified_at = timezone.now()
                ar.last_modified_by = user.get_full_name()

                ar.save()

                persisted = _db_values(ar, *ACCOMMODATION_AR_FIELDS)
                log_dedup_persistence_check(
                    "AccommodationDuplicateGroup."
                    "_handle_linked_accommodation_requests: AR linked",
                    group_id=self.pk,
                    ar_pk=ar.pk,
                    accommodation_pk=accommodation.pk,
                    new_principal_pk=new_principal.pk,
                    before=before,
                    changes={
                        field: (getattr(ar, field), persisted.get(field))
                        for field in ACCOMMODATION_AR_FIELDS
                    },
                )


class GuestDuplicateGroupManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        guests_cannot_view = MvPerson.objects.exclude(
            MvPerson.objects._filter_by_ltla_name(ltla_names)
        )
        return ~Q(guests__in=guests_cannot_view) & ~Q(
            principal_record__in=guests_cannot_view
        )

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        guests_cannot_view = MvPerson.objects.exclude(
            MvPerson.objects._filter_by_utla_name(utla_names)
        )
        return ~Q(guests__in=guests_cannot_view) & ~Q(
            principal_record__in=guests_cannot_view
        )

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        guests_cannot_view = MvPerson.objects.exclude(
            MvPerson.objects._filter_by_viewer_group_name(viewer_group_names)
        )
        return ~Q(guests__in=guests_cannot_view) & ~Q(
            principal_record__in=guests_cannot_view
        )


class GuestDuplicateGroup(models.Model):
    objects = GuestDuplicateGroupManager()

    principal_record = models.ForeignKey(
        "ontology.MvPerson",
        on_delete=models.SET_NULL,
        null=True,
        db_column="principal_record_id",
    )
    guests = ManyToManyField(
        "ontology.MvPerson",
        db_table="ontology_guest_to_duplicate_group",
        related_name="duplicate_group",
    )
    created_at = models.DateTimeField(default=timezone.now)
    source_guest_ar_mapping = ArrayField(models.JSONField(), default=list)
    archived_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(null=False, default=False)

    def format_guest_names(self, guests):
        names = [str(g.get_full_name()) for g in guests]
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        names.sort()
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return f"{', '.join(names[:-1])} and {names[-1]}"

    @record_operation_outcome("guest")
    @transaction.atomic
    def deduplicate(self, principal_record_values: dict[str, Any], user: User):  # noqa: C901
        handle_deduplication_exceptions(user, self.principal_record, self.guests)

        guests: list[MvPerson] = list(self.guests.all())

        log_dedup_event(
            "GuestDuplicateGroup.deduplicate: started",
            group_id=self.pk,
            user=user.pk,
            duplicate_record_count=len(guests),
            duplicate_record_pks=[g.pk for g in guests],
            target_ar_pk=getattr(
                principal_record_values.get("accommodation_request"), "pk", None
            ),
        )

        # create new principal record values
        principal_record_values["is_principal"] = True
        principal_record_values["notional_data"] = any(
            guest.notional_data for guest in guests
        )
        principal_record_values["adverse_rematch"] = any(
            guest.adverse_rematch for guest in guests
        )
        principal_record_values["disability_flag"] = any(
            guest.disability_flag for guest in guests
        )
        principal_record_values["is_uam"] = any(guest.is_uam for guest in guests)
        principal_record_values["wheelchair_required"] = any(
            guest.wheelchair_required for guest in guests
        )
        principal_record_values["source"] = list(
            reduce(
                lambda sources, guest: sources + list(guest.source or []),
                guests,
                [],
            )
        )
        principal_record_values["viewer_group_names"] = list(
            reduce(
                lambda viewer_group_names, guest: viewer_group_names
                + list(guest.viewer_group_names or []),
                guests,
                [],
            )
        )
        principal_record_values["gwf"] = list(
            reduce(
                lambda gwfs, guest: gwfs + list(guest.gwf or []),
                guests,
                [],
            )
        )
        principal_record_values["nationality"] = list(
            reduce(
                lambda nationality, guest: nationality + list(guest.nationality or []),
                guests,
                [],
            )
        )
        principal_record_values["application_number"] = list(
            reduce(
                lambda application_number, guest: application_number
                + list(guest.application_number or []),
                guests,
                [],
            )
        )
        principal_record_values["primary_application_numbers"] = list(
            reduce(
                lambda primary_application_numbers, guest: primary_application_numbers
                + list(guest.primary_application_numbers or []),
                guests,
                [],
            )
        )
        principal_record_values["created_at"] = min(
            (guest.created_at for guest in guests if guest.created_at is not None),
            default=None,
        )
        principal_record_values["created_by"] = user.email
        if "date_of_birth" in principal_record_values:
            principal_record_values["age"] = calculate_age(
                principal_record_values["date_of_birth"]
            )
        principal_record_values["can_be_contacted_by_phone"] = (
            "Yes"
            if any(guest.can_be_contacted_by_phone == "Yes" for guest in guests)
            else "No"
        )

        # create new principal record
        new_principal = MvPerson.objects.create(
            id=f"person-{uuid.uuid4()}",
            **principal_record_values,
        )

        # save to get a pk
        new_principal.save()

        log_dedup_persistence_check(
            "GuestDuplicateGroup.deduplicate: new principal created",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            changes={
                "new_principal_id": (
                    new_principal.pk,
                    _db_values(new_principal, "id").get("id"),
                ),
            },
        )

        # Handle linked records
        self._handle_linked_sponsorship_certification_forms(new_principal, guests)
        self._handle_linked_accommodation_requests(
            new_principal,
            guests,
            principal_record_values.get("accommodation_request"),
            user,
        )
        self._handle_linked_uans(
            guests, principal_record_values.get("accommodation_request")
        )

        # flag constituent records as duplicates
        for guest in guests:
            guest.is_principal = False
            guest.save()
            log_dedup_persistence_check(
                "GuestDuplicateGroup.deduplicate: duplicate record merged",
                group_id=self.pk,
                duplicate_record_pk=guest.pk,
                new_principal_pk=new_principal.pk,
                changes={
                    "is_principal": (
                        guest.is_principal,
                        _db_values(guest, "is_principal").get("is_principal"),
                    ),
                },
            )

        # Save data to duplicate group
        self.principal_record = new_principal
        self.principal_record.save()
        self.save()

        log_dedup_persistence_check(
            "GuestDuplicateGroup.deduplicate: finished",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            changes={
                "principal_record_id": (
                    self.principal_record_id,
                    _db_values(self, "principal_record_id").get("principal_record_id"),
                ),
            },
        )

        # Add interactions for deduplication event
        for record in guests:
            others = [g for g in guests if g != record]
            if len(others) == 1:
                other_name = others[0].get_full_name()
                note = (
                    f"This record, and guest record {other_name}"
                    f" were marked as duplicates. "
                    f"New principal record is {new_principal.get_full_name()}."
                )
            else:
                other_names = self.format_guest_names(others)
                note = (
                    f"This record, and guest records {other_names}"
                    f" were marked as duplicates. "
                    f"New principal record is {new_principal.get_full_name()}."
                )
            MvInteraction.objects.create(
                interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                created_by=user,
                title="Record deduplicated",
                interaction_notes=note,
                linked_guest=record,
            )

        MvInteraction.objects.create(
            interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
            interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
            created_by=user,
            title="Record deduplicated",
            interaction_notes=(
                f"This record was created after guest records "
                f"{self.format_guest_names(guests)} "
                f"were marked as duplicates."
            ),
            linked_guest=new_principal,
        )

    @record_operation_outcome("guest")
    @transaction.atomic
    def undo_deduplication(self, user: User):  # noqa: C901
        check_user_is_not_none(user)

        guests: list[MvPerson] = list(self.guests.all())

        log_dedup_event(
            "GuestDuplicateGroup.undo_deduplication: started",
            group_id=self.pk,
            user=user.pk,
            principal_record_id=self.principal_record_id,
            restored_record_pks=[g.pk for g in guests],
            source_guest_ar_mapping=self.source_guest_ar_mapping,
        )

        for guest in guests:
            guest.is_principal = True
            guest.save()
            log_dedup_persistence_check(
                "GuestDuplicateGroup.undo_deduplication: duplicate record restored",
                group_id=self.pk,
                restored_record_pk=guest.pk,
                changes={
                    "is_principal": (
                        guest.is_principal,
                        _db_values(guest, "is_principal").get("is_principal"),
                    ),
                },
            )

        # Links UANs back to correct ARs
        self._undo_deduplication_handle_linked_uans(guests)

        # Links ARs back to relevant sponsor
        self._undo_deduplication_handle_linked_accommodation_requests(guests, user)

        # Archives old principal record
        self.principal_record.is_principal = False
        self.principal_record.is_archived = True
        archived_time = timezone.now()
        self.principal_record.archived_at = archived_time
        self.principal_record.save()
        self.is_archived = True
        self.archived_at = archived_time
        self.save()

        log_dedup_persistence_check(
            "GuestDuplicateGroup.undo_deduplication: finished",
            group_id=self.pk,
            changes={},
        )

        # Add interactions for undo deduplication event
        for record in guests:
            others = [g for g in guests if g != record]
            if len(others) == 1:
                other_name = others[0].get_full_name()
                note = (
                    f"This record, and guest record {other_name} "
                    f"were restored as separate principal records. "
                    f"A principal record combining data from both was deleted."
                )
            else:
                other_names = self.format_guest_names(others)
                note = (
                    f"This record, and guest record {other_names} "
                    f"were restored as separate principal records. "
                    f"A principal record combining data from both was deleted."
                )
            MvInteraction.objects.create(
                interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
                interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
                created_by=user,
                title="Deduplication undone",
                interaction_notes=note,
                linked_guest=record,
            )

    def has_blocking_reassignment_for_undo(self, guest_id: str) -> bool:
        return (
            ReassignmentRequest.objects.filter(guests=guest_id)
            .filter(
                Q(outcome=ReassignmentRequest.Outcome.PENDING)
                | (
                    Q(outcome=ReassignmentRequest.Outcome.ACCEPTED)
                    & Q(responded_at__gte=self.created_at)
                )
            )
            .exists()
        )

    def has_blocking_multi_la_accommodation_request(self, guest_id: str) -> bool:
        return MvPerson.objects.filter(
            pk=guest_id,
            accommodation_request__ltla_name__len__gt=1,
        ).exists()

    def has_blocking_reassignment_for_dedupe(self, guest_id: str) -> bool:
        return (
            ReassignmentRequest.objects.filter(guests=guest_id)
            .filter(Q(outcome=ReassignmentRequest.Outcome.PENDING))
            .exists()
        )

    def can_undo_deduplication(self, guest_id: str) -> bool:
        return not self.has_blocking_reassignment_for_undo(
            guest_id
        ) and not self.has_blocking_multi_la_accommodation_request(guest_id)

    def can_deduplicate(self, guest_id: str) -> bool:
        return not self.has_blocking_reassignment_for_dedupe(guest_id)

    def _collate_ars(
        self, target_ar: MvAccommodationRequest | None, guests: list[MvPerson]
    ):
        affected_ars = {target_ar.pk: target_ar} if target_ar else {}
        for guest in guests:
            ar = guest.accommodation_request
            if ar and ar.pk not in affected_ars:
                affected_ars[ar.pk] = ar
        log_dedup_event(
            "GuestDuplicateGroup._collate_ars: affected ARs collated",
            group_id=self.pk,
            target_ar_pk=getattr(target_ar, "pk", None),
            affected_ar_pks=list(affected_ars.keys()),
        )
        return affected_ars

    def _remove_duplicates_from_ars(
        self, affected_ars: Dict[Any, MvAccommodationRequest], guests: list[MvPerson]
    ):
        guest_pks = [g.pk for g in guests]
        for current_ar in affected_ars.values():
            if current_ar.person_id is None:
                current_ar.person_id = []
                log_dedup_event(
                    "GuestDuplicateGroup._remove_duplicates_from_ars: "
                    "AR person list cleared",
                    group_id=self.pk,
                    ar_pk=current_ar.pk,
                    guest_pks=guest_pks,
                    person_id_before=None,
                    person_id_in_memory=[],
                    note=(
                        "person_id was None and has been set to [] in memory. "
                        "Not saved in this method; persisted by the save pass "
                        "in _handle_linked_accommodation_requests."
                    ),
                )
                continue

            before_person_id = list(current_ar.person_id)
            for guest in guests:
                if guest.pk in current_ar.person_id:
                    current_ar.person_id.remove(guest.pk)

            log_dedup_event(
                "GuestDuplicateGroup._remove_duplicates_from_ars: "
                "AR person list updated",
                group_id=self.pk,
                ar_pk=current_ar.pk,
                guest_pks=guest_pks,
                person_id_before=before_person_id,
                person_id_in_memory=list(current_ar.person_id or []),
                note=(
                    "Duplicate guests removed from person_id in memory. Not "
                    "saved in this method; persisted by the save pass in "
                    "_handle_linked_accommodation_requests - see its "
                    "'AR persisted' log to confirm it stuck."
                ),
            )

    def _link_new_principal_to_ar(
        self, target_ar: MvAccommodationRequest | None, new_principal: MvPerson
    ):
        if target_ar:
            before_accommodation_request_id = new_principal.accommodation_request_id
            before_person_id = list(target_ar.person_id or [])
            new_principal.accommodation_request = target_ar
            new_principal.save()

            if target_ar.person_id is None:
                target_ar.person_id = []

            if new_principal.pk not in target_ar.person_id:
                target_ar.person_id.append(new_principal.pk)

            log_dedup_persistence_check(
                "GuestDuplicateGroup._link_new_principal_to_ar: "
                "new principal linked to AR",
                group_id=self.pk,
                target_ar_pk=target_ar.pk,
                new_principal_pk=new_principal.pk,
                principal_accommodation_request_id_before=(
                    before_accommodation_request_id
                ),
                target_ar_person_id_before=before_person_id,
                target_ar_person_id_in_memory=list(target_ar.person_id or []),
                note=(
                    "target_ar is NOT saved here; its person_id is persisted "
                    "by the save pass in _handle_linked_accommodation_requests. "
                    "Only the new_principal link is verified below."
                ),
                changes={
                    "principal_accommodation_request_id": (
                        new_principal.accommodation_request_id,
                        _db_values(new_principal, "accommodation_request_id").get(
                            "accommodation_request_id"
                        ),
                    ),
                },
            )

    def _update_ar_titles(
        self,
        affected_ars: Dict[Any, MvAccommodationRequest],
        ar_to_original_primary: Dict[Any, MvPerson | None],
        guests: list[MvPerson],
        target_ar: MvAccommodationRequest | None,
        new_principal: MvPerson,
    ):
        for current_ar in affected_ars.values():
            before_person_id = list(current_ar.person_id or [])
            current_ar.update_number_of_people()

            orig_primary = ar_to_original_primary.get(current_ar.pk)
            guest_pks = {g.pk for g in guests}
            orig_primary_was_deduped = orig_primary and orig_primary.pk in guest_pks

            remaining_eldest = current_ar.get_primary_contact_person()

            if current_ar == target_ar:
                if orig_primary_was_deduped:
                    current_ar.update_primary_contact(new_principal)
            else:
                if not remaining_eldest:
                    current_ar.primary_contact_first_name = None
                    current_ar.primary_contact_last_name = None
                    current_ar.primary_contact_email = None
                    current_ar.number_of_people = 0
                elif orig_primary_was_deduped:
                    current_ar.update_primary_contact(remaining_eldest)

            current_ar.update_title()

            log_dedup_event(
                "GuestDuplicateGroup._update_ar_titles: AR title and contact updated",
                group_id=self.pk,
                ar_pk=current_ar.pk,
                is_target_ar=current_ar == target_ar,
                original_primary_was_deduplicated=bool(orig_primary_was_deduped),
                person_id_before=before_person_id,
                person_id_in_memory=list(current_ar.person_id or []),
                number_of_people_in_memory=current_ar.number_of_people,
                note=(
                    "In-memory state after the title/contact update. The AR "
                    "is persisted by the save pass in "
                    "_handle_linked_accommodation_requests; see its "
                    "'AR persisted' log for the persistence check."
                ),
            )

    def _handle_linked_accommodation_requests(
        self,
        new_principal: MvPerson,
        guests: list[MvPerson],
        ar: MvAccommodationRequest | None,
        user: User,
    ):
        # target AR is arg (if user selected) or first guest AR (auto selected)
        target_ar = ar
        if not target_ar:
            for guest in guests:
                if guest.accommodation_request:
                    target_ar = guest.accommodation_request
                    break

        log_dedup_event(
            "GuestDuplicateGroup._handle_linked_accommodation_requests: started",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            guest_pks=[g.pk for g in guests],
            explicit_target_ar_pk=getattr(ar, "pk", None),
            resolved_target_ar_pk=getattr(target_ar, "pk", None),
        )

        affected_ars = self._collate_ars(target_ar, guests)

        ar_to_original_primary = {
            pk: ar.get_primary_contact_person() for pk, ar in affected_ars.items()
        }

        self._remove_duplicates_from_ars(affected_ars, guests)

        self._link_new_principal_to_ar(target_ar, new_principal)

        self._update_ar_titles(
            affected_ars, ar_to_original_primary, guests, target_ar, new_principal
        )

        # Persist every AR mutated above
        for affected_ar in affected_ars.values():
            affected_ar.checks_status = (
                affected_ar.determine_checks_status_from_linked_objects()
            )
            affected_ar.last_modified_at = timezone.now()
            affected_ar.last_modified_by = user.get_full_name()
            affected_ar.save()
            persisted = _db_values(affected_ar, "person_id", "number_of_people")
            log_dedup_persistence_check(
                "GuestDuplicateGroup._handle_linked_accommodation_requests: "
                "AR persisted",
                group_id=self.pk,
                ar_pk=affected_ar.pk,
                changes={
                    "person_id": (
                        list(affected_ar.person_id or []),
                        persisted.get("person_id"),
                    ),
                    "number_of_people": (
                        affected_ar.number_of_people,
                        persisted.get("number_of_people"),
                    ),
                },
            )

        if target_ar:
            formatted_date = date_format(self.created_at, "j F Y")
            principal_name = new_principal.get_full_name()
            guests_on_target_ar = [
                g for g in guests if g.accommodation_request == target_ar
            ]

            guests_by_unselected_ar: dict[str, list[MvPerson]] = {}
            for guest in guests:
                if (
                    guest.accommodation_request
                    and guest.accommodation_request != target_ar
                ):
                    guests_by_unselected_ar.setdefault(
                        guest.accommodation_request_id, []
                    ).append(guest)

            MvInteraction.objects.bulk_create(
                [
                    MvInteraction(
                        interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                        interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                        title="Record deduplicated",
                        created_by=user,
                        linked_accommodation_request=ar_guests[0].accommodation_request,
                        interaction_notes=self._build_unselected_ar_interaction_notes(
                            ar_guests, formatted_date, principal_name
                        ),
                    )
                    for ar_guests in guests_by_unselected_ar.values()
                ]
            )

            MvInteraction.objects.create(
                interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATED,
                title="Record deduplicated",
                created_by=user,
                linked_accommodation_request=target_ar,
                interaction_notes=self._build_target_ar_interaction_notes(
                    guests_on_target_ar, guests, formatted_date, principal_name
                ),
            )

    def _build_unselected_ar_interaction_notes(
        self,
        ar_guests: list[MvPerson],
        formatted_date: str,
        principal_name: str | None,
    ) -> str:
        if len(ar_guests) == 1:
            return (
                f"{ar_guests[0].get_full_name()} was moved to another accommodation"
                f" request as part of a deduplication on {formatted_date}.\n\n"
                f"The guest was marked as a duplicate and a new principal guest"
                f" record created for {principal_name}."
            )
        named_guests = [(g.get_full_name() or "", g.id) for g in ar_guests]
        named_guests.sort(key=lambda item: (item[0].casefold(), item[1]))
        bullet_list = "\n".join(f"• {name}" for name, _ in named_guests)
        return (
            f"{bullet_list}\n\nwere moved to another accommodation request as part"
            f" of a deduplication on {formatted_date}.\n\n"
            f"New principal guest record is {principal_name}."
        )

    def _build_target_ar_interaction_notes(
        self,
        guests_on_target_ar: list[MvPerson],
        all_guests: list[MvPerson],
        formatted_date: str,
        principal_name: str | None,
    ) -> str:
        multiple = len(guests_on_target_ar) > 1
        notes = (
            f"{self.format_guest_names(guests_on_target_ar)}"
            f" {'were' if multiple else 'was'} marked as"
            f" {'duplicates' if multiple else 'a duplicate'}"
            f" on {formatted_date} and replaced"
            f" by a new principal record, {principal_name}."
        )
        if guests_on_target_ar != all_guests:
            notes += (
                f"\n\nThis principal record was created after guest records"
                f" {self.format_guest_names(all_guests)} were marked as duplicates."
            )
        return notes

    def _handle_linked_sponsorship_certification_forms(
        self, new_principal: MvPerson, guests: list[MvPerson]
    ):
        """
        Links the sponsorship certification forms of guests to the new principal,
        without breaking old links
        """
        new_principal.sponsorship_certification_number_id = list(
            reduce(
                lambda cert_numbers, guest: cert_numbers
                + list(guest.sponsorship_certification_number_id or []),
                guests,
                [],
            )
        )

        log_dedup_event(
            "GuestDuplicateGroup._handle_linked_sponsorship_certification_forms: "
            "cert forms set",
            group_id=self.pk,
            new_principal_pk=new_principal.pk,
            cert_numbers_in_memory=(new_principal.sponsorship_certification_number_id),
            cert_numbers_persisted=_db_values(
                new_principal, "sponsorship_certification_number_id"
            ).get("sponsorship_certification_number_id"),
            note=(
                "Set on new_principal in memory only. Not saved here; "
                "persisted by the later principal_record.save() in "
                "deduplicate(), so in-memory and DB values differ now by "
                "design."
            ),
        )

    def _handle_linked_uans(
        self, guests: list[MvPerson], ar: MvAccommodationRequest | None
    ):
        if ar is None:
            log_dedup_event(
                "GuestDuplicateGroup._handle_linked_uans: skipped",
                group_id=self.pk,
                note="No target accommodation request, nothing to do.",
            )
            return

        log_dedup_event(
            "GuestDuplicateGroup._handle_linked_uans: started",
            group_id=self.pk,
            target_ar_pk=ar.pk,
            guest_pks=[g.pk for g in guests],
        )

        for guest in guests:
            if guest.accommodation_request == ar:
                continue
            else:
                if guest.application_number:
                    before_source_uans = list(
                        guest.accommodation_request.unique_application_number or []
                    )
                    before_target_uans = list(ar.unique_application_number or [])
                    before_target_sponsor_id = list(ar.sponsor_id or [])
                    # remove uans from unselected AR
                    guest.accommodation_request.unique_application_number = [
                        g_uan
                        for g_uan in (
                            guest.accommodation_request.unique_application_number
                        )
                        if g_uan not in guest.application_number
                    ]

                    for uan in guest.application_number:
                        # add uans to selected AR
                        ar.unique_application_number.append(uan)

                        # add sponsors related to the same uans to the selected AR
                        sponsors = MvVolunteer.objects.filter(
                            application_unique_application_number__contains=[uan]
                        )
                        for sponsor in sponsors:
                            ar.sponsor_id.append(sponsor.pk)
                        guest.accommodation_request.save()
                        ar.save()

                    persisted_source = _db_values(
                        guest.accommodation_request, "unique_application_number"
                    )
                    persisted_target = _db_values(
                        ar, "unique_application_number", "sponsor_id"
                    )
                    log_dedup_persistence_check(
                        "GuestDuplicateGroup._handle_linked_uans: "
                        "guest UANs moved to target AR",
                        group_id=self.pk,
                        guest_pk=guest.pk,
                        guest_application_number=guest.application_number,
                        source_ar_pk=guest.accommodation_request_id,
                        target_ar_pk=ar.pk,
                        source_unique_application_number_before=(before_source_uans),
                        target_unique_application_number_before=(before_target_uans),
                        target_sponsor_id_before=before_target_sponsor_id,
                        changes={
                            "source_unique_application_number": (
                                guest.accommodation_request.unique_application_number,
                                persisted_source.get("unique_application_number"),
                            ),
                            "target_unique_application_number": (
                                ar.unique_application_number,
                                persisted_target.get("unique_application_number"),
                            ),
                            "target_sponsor_id": (
                                list(ar.sponsor_id or []),
                                persisted_target.get("sponsor_id"),
                            ),
                        },
                    )

    def _undo_deduplication_handle_linked_uans(self, guests: list[MvPerson]):
        log_dedup_event(
            "GuestDuplicateGroup._undo_deduplication_handle_linked_uans: started",
            group_id=self.pk,
            guest_pks=[g.pk for g in guests],
        )
        for guest in guests:
            # Collate uans belonging to other guests in the dedupe process
            # and remove from the AR
            other_guest_uans = sum(
                [g.application_number or [] for g in guests if g != guest], []
            )

            before_uans = list(
                guest.accommodation_request.unique_application_number or []
            )
            before_sponsor_id = list(guest.accommodation_request.sponsor_id or [])

            current_uan_list = list(
                guest.accommodation_request.unique_application_number or []
            )
            external_uans = set(
                [g_uan for g_uan in current_uan_list if g_uan not in other_guest_uans]
            )

            guest.accommodation_request.unique_application_number = list(
                external_uans | set(guest.application_number or [])
            )

            guest.accommodation_request.save()

            # Collate sponsors related to the same uans and remove from AR
            if guest.accommodation_request.sponsor_id:
                sponsors_to_remove = MvVolunteer.objects.filter(
                    application_unique_application_number__overlap=(other_guest_uans)
                )
                s_to_remove_ids = [s.pk for s in sponsors_to_remove]
                updated_sponsors = [
                    s_id
                    for s_id in guest.accommodation_request.sponsor_id
                    if s_id not in s_to_remove_ids
                ]
                guest.accommodation_request.sponsor_id = updated_sponsors

                guest.accommodation_request.save()
                guest.save()

            persisted = _db_values(
                guest.accommodation_request,
                "unique_application_number",
                "sponsor_id",
            )
            log_dedup_persistence_check(
                "GuestDuplicateGroup._undo_deduplication_handle_linked_uans: "
                "guest UANs restored",
                group_id=self.pk,
                guest_pk=guest.pk,
                ar_pk=guest.accommodation_request_id,
                guest_application_number=guest.application_number,
                other_guest_uans=other_guest_uans,
                unique_application_number_before=before_uans,
                sponsor_id_before=before_sponsor_id,
                changes={
                    "unique_application_number": (
                        guest.accommodation_request.unique_application_number,
                        persisted.get("unique_application_number"),
                    ),
                    "sponsor_id": (
                        list(guest.accommodation_request.sponsor_id or []),
                        persisted.get("sponsor_id"),
                    ),
                },
            )

    def _undo_deduplication_handle_linked_accommodation_requests(
        self, guests: list[MvPerson], user
    ):
        affected_ars = self._collate_ars(None, guests)
        # Exclude closed statuses except Closed - Empty Group
        exclude_statuses = [
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
        ]

        for ar in affected_ars.values():
            before_person_id = list(ar.person_id or [])
            if ar.person_id is None:
                ar.person_id = []

            principal_in_person_id = (
                bool(self.principal_record.pk)
                and self.principal_record.pk in ar.person_id
            )
            if self.principal_record.pk and self.principal_record.pk in ar.person_id:
                ar.person_id.remove(self.principal_record.pk)

            for guest in guests:
                if guest.accommodation_request_id == ar.pk:
                    guest_pk = str(guest.pk)
                    if guest_pk not in ar.person_id:
                        ar.person_id.append(guest_pk)

            ar.update_number_of_people()
            ar.update_primary_contact(ar.get_primary_contact_person())
            ar.update_title()
            ar.checks_status = ar.determine_checks_status_from_linked_objects(
                excluded_statuses=exclude_statuses
            )
            ar.last_modified_at = timezone.now()
            ar.last_modified_by = user.get_full_name()

            persisted_pre_save = _db_values(ar, "person_id", "number_of_people")
            log_dedup_event(
                "GuestDuplicateGroup._undo_deduplication_handle_linked_accommodation_"
                "requests: AR person list rebuilt",
                group_id=self.pk,
                ar_pk=ar.pk,
                principal_record_id=self.principal_record_id,
                principal_was_in_person_id=principal_in_person_id,
                person_id_before=before_person_id,
                person_id_in_memory=list(ar.person_id or []),
                person_id_persisted=persisted_pre_save.get("person_id"),
                number_of_people_in_memory=ar.number_of_people,
                note=(
                    "Not yet saved; see the ': AR saved' log for the "
                    "post-save persistence check."
                ),
            )

            for guest in guests:
                if guest.pk in ar.person_id:
                    MvInteraction.objects.create(
                        interaction_contact=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
                        interaction_type=MvInteraction.InteractionContact.RECORD_DEDUPLICATION_UNDONE,
                        created_by=user,
                        title="Guest restored",
                        interaction_notes=f"{guest.get_full_name()} was restored to "
                        f"this accommodation request by undoing a "
                        f"deduplication.",
                        linked_accommodation_request=ar,
                    )

            ar.save()

            persisted_post_save = _db_values(ar, "person_id", "number_of_people")
            log_dedup_persistence_check(
                "GuestDuplicateGroup._undo_deduplication_handle_linked_accommodation_"
                "requests: AR saved",
                group_id=self.pk,
                ar_pk=ar.pk,
                changes={
                    "person_id": (
                        list(ar.person_id or []),
                        persisted_post_save.get("person_id"),
                    ),
                    "number_of_people": (
                        ar.number_of_people,
                        persisted_post_save.get("number_of_people"),
                    ),
                },
            )
