import logging
import uuid
from copy import deepcopy
from datetime import datetime, timezone

from django.contrib import admin
from django.db.models import Q, QuerySet

from accommodation_requests.safeguarding_utils import NotificationData, loop_and_raise
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    SafeguardingNotification,
)

logger = logging.getLogger(__name__)
GO_LIVE_DATE = datetime(2025, 9, 15, tzinfo=timezone.utc)


@admin.action(description="Duplicate check onto the principal record")
def solve_duplicate_record_sponsor_checks(
    modeladmin, request, queryset: QuerySet[DevCheckV2]
):
    for check in queryset:
        messages = []
        if check.check_type.id == CheckType.Id.SPONSOR_DBS:
            messages = process_single_sponsor_check(check)

        if check.check_type.id == CheckType.Id.ACCOMM_EXISTS:
            messages = process_single_accommodation_exists_check(check)

        if check.check_type.id == CheckType.Id.ACCOMM_SUITABLE:
            messages = process_single_accommodation_suitable_check(check)

        for message in messages:
            modeladmin.message_user(request, message)
            logger.info(message)


def process_single_sponsor_check(check: DevCheckV2) -> list[str]:
    messages = []
    messages.append(f"[{check.id}]: Start - Solving check on duplicate record")

    if check.check_type.id != CheckType.Id.SPONSOR_DBS:
        messages.append(f"[{check.id}]: Is not a Sponsor DBS check")

        return messages

    if not check.create_at:
        messages.append(f"[{check.id}]: Missing create_at date")

        return messages
    elif check.create_at < GO_LIVE_DATE:
        messages.append(f"[{check.id}]: Created before share 'Go Live' date")

        return messages

    duplicate_linked_sponsors = check.sponsor.filter(is_principal=False)
    if not duplicate_linked_sponsors.exists():
        messages.append(f"[{check.id}]: Is not linked to duplicate sponsor record")

        return messages

    messages.append(
        (
            f"[{check.id}]: Has {duplicate_linked_sponsors.count()} duplicate "
            "linked sponsor records"
        )
    )

    for sponsor in duplicate_linked_sponsors:
        master_records = sponsor.master_record.all()

        if not master_records.exists():
            messages.append(
                (
                    f"[{check.id}]:Sponsor with id={sponsor.id} marked with "
                    "is_principal=False but is missing a SponsorMasterRecord"
                ),
            )

            return messages

        for master_record in master_records:
            # get principal sponsor off the master record
            principal_sponsor = MvVolunteer.objects.filter(
                id=master_record.principal_record_id
            ).first()

            if not principal_sponsor:
                messages.append(
                    (
                        f"[{check.id}]: SponsorMasterRecord with id="
                        f"{master_record.record_id} has no principal sponsor"
                    ),
                )

                return messages

            pricipal_has_check = principal_sponsor.checks.filter(
                check_type=check.check_type
            )

            if pricipal_has_check.exists():
                messages.append(
                    (
                        f"[{check.id}]: Principal sponsor with id="
                        f"{principal_sponsor.id} already has a check of "
                        "this type, not duplicating"
                    ),
                )

                return messages

            # duplicate the check
            new_check = deepcopy(check)
            new_check.id = uuid.uuid4()
            new_check.save()

            new_check.sponsor.set([principal_sponsor])
            messages.append(
                (
                    f"[{check.id}]: Created new check with id={new_check.id} "
                    f"linked to principal sponsor with id={principal_sponsor.id} "
                    f"of duplicate sponsor with id={sponsor.id}"
                ),
            )

            # if appropriate, also create an escalation for this check
            if new_check.check_status == DevCheckV2.CheckStatus.FAILED:
                messages.append(
                    (
                        f"[{check.id}]: Creating escalation for new failed check "
                        f"with id={new_check.id}"
                    ),
                )

                notification_data = NotificationData(
                    alert_type=SafeguardingNotification.AlertType.SAFEGUARDING_CHECK,
                    check=new_check,
                    sponsor=principal_sponsor,
                )

                # The loop and raise function requires an AR to be passed in as in
                # the system a check is always raised via an AR. Sponsor checks
                # apply to all ARs the sponsor is linked to, and this function will
                # make sure the escalation is raised against all guests on any AR
                # so just pass in a single one, it doesn't matter which.
                accommodation_request = MvAccommodationRequest.objects.filter(
                    Q(active_host_id=principal_sponsor.id)
                    | Q(primary_sponsor_id=principal_sponsor.id)
                    | Q(sponsor_id__contains=[principal_sponsor.id])
                ).first()

                if not accommodation_request:
                    messages.append(
                        (
                            f"[{check.id}]: Escalation not raised for new failed "
                            f"check with id={new_check.id} linked against principal"
                            f" sponsor with id={principal_sponsor.id}. Principal "
                            "sponsor not attached to any ARs"
                        ),
                    )

                    return messages

                loop_and_raise(accommodation_request, notification_data)

                messages.append(
                    (
                        f"[{check.id}]: Escalation handled for new failed check "
                        f"with id={new_check.id} linked against principal sponsor w"
                        f"ith id={principal_sponsor.id}"
                    ),
                )

            messages.append(
                f"[{check.id}]: End - Solving check on duplicate record",
            )

    return messages


def process_single_accommodation_exists_check(check: DevCheckV2) -> list[str]:
    messages = []
    messages.append(f"[{check.id}]: Start - Solving check on duplicate record")

    if check.check_type.id != CheckType.Id.ACCOMM_EXISTS:
        messages.append(f"[{check.id}]: Is not an Accommodation exists type check")

        return messages

    if not check.create_at:
        messages.append(f"[{check.id}]: Missing create_at date")

        return messages
    elif check.create_at < GO_LIVE_DATE:
        messages.append(f"[{check.id}]: Created before share 'Go Live' date")

        return messages

    duplicate_linked_accommodation = check.accommodation.filter(is_principal=False)
    if not duplicate_linked_accommodation.exists():
        messages.append(
            f"[{check.id}]: Is not linked to duplicate accommodation record"
        )

        return messages

    messages.append(
        (
            f"[{check.id}]: Has {duplicate_linked_accommodation.count()} duplicate "
            "linked accommodation records"
        )
    )

    for accommodation in duplicate_linked_accommodation:
        master_records = accommodation.master_record.all()

        if not master_records.exists():
            messages.append(
                (
                    f"[{check.id}]:Accommodation with id={accommodation.id} marked "
                    "with is_principal=False but is missing a AccommodationMasterRecord"
                ),
            )

            return messages

        for master_record in master_records:
            # get principal accommodation off the master record
            principal_accommodation = MvAccommodation.objects.filter(
                id=master_record.principal_record_id
            ).first()

            if not principal_accommodation:
                messages.append(
                    (
                        f"[{check.id}]: AccommodationMasterRecord with id="
                        f"{master_record.record_id} has no principal accommodation"
                    ),
                )

                return messages

            pricipal_has_check = principal_accommodation.checks.filter(
                check_type=check.check_type
            )

            if pricipal_has_check.exists():
                messages.append(
                    (
                        f"[{check.id}]: Principal accommodation with id="
                        f"{principal_accommodation.id} already has a check of "
                        "this type, not duplicating"
                    ),
                )

                return messages

            # duplicate the check
            new_check = deepcopy(check)
            new_check.id = uuid.uuid4()
            new_check.save()

            new_check.accommodation.set([principal_accommodation])
            messages.append(
                (
                    f"[{check.id}]: Created new check with id={new_check.id} "
                    "linked to principal accommodation with "
                    f"id={principal_accommodation.id} "
                    f"of duplicate sponsor with id={accommodation.id}"
                ),
            )

            # if appropriate, also create an escalation for this check
            if new_check.check_status == DevCheckV2.CheckStatus.FAILED:
                messages.append(
                    (
                        f"[{check.id}]: Creating escalation for new failed check "
                        f"with id={new_check.id}"
                    ),
                )

                notification_data = NotificationData(
                    alert_type=SafeguardingNotification.AlertType.SAFEGUARDING_CHECK,
                    check=new_check,
                    accommodation=principal_accommodation,
                )

                # The loop and raise function requires an AR to be passed in as in
                # the system a check is always raised via an AR. Acc Exists checks
                # apply to all ARs the acc is linked to, and this function will
                # make sure the escalation is raised against all guests on any AR
                # so just pass in a single one, it doesn't matter which.
                accommodation_request = MvAccommodationRequest.objects.filter(
                    Q(primary_accommodation_id=principal_accommodation.id)
                    | Q(accommodation_id__contains=[principal_accommodation.id])
                ).first()

                if not accommodation_request:
                    messages.append(
                        (
                            f"[{check.id}]: Escalation not raised for new failed "
                            f"check with id={new_check.id} linked against principal"
                            f" accommodation with id={principal_accommodation.id}. "
                            "Principal accommodation not attached to any ARs"
                        ),
                    )

                    return messages

                loop_and_raise(accommodation_request, notification_data)

                messages.append(
                    (
                        f"[{check.id}]: Escalation handled for new failed check "
                        f"with id={new_check.id} linked against principal accommodation"
                        f" with id={principal_accommodation.id}"
                    ),
                )

            messages.append(
                f"[{check.id}]: End - Solving check on duplicate record",
            )

    return messages


def process_single_accommodation_suitable_check(check: DevCheckV2) -> list[str]:
    messages = []
    messages.append(f"[{check.id}]: Start - Solving check on duplicate record")

    if check.check_type.id != CheckType.Id.ACCOMM_SUITABLE:
        messages.append(f"[{check.id}]: Is not an Accommodation suitable type check")

        return messages

    if not check.create_at:
        messages.append(f"[{check.id}]: Missing create_at date")

        return messages
    elif check.create_at < GO_LIVE_DATE:
        messages.append(f"[{check.id}]: Created before share 'Go Live' date")

        return messages

    duplicate_linked_accommodation = check.accommodation.filter(is_principal=False)
    if not duplicate_linked_accommodation.exists():
        messages.append(
            f"[{check.id}]: Is not linked to duplicate accommodation record"
        )

        return messages

    messages.append(
        (
            f"[{check.id}]: Has {duplicate_linked_accommodation.count()} duplicate "
            "linked accommodation records"
        )
    )

    for accommodation in duplicate_linked_accommodation:
        master_records = accommodation.master_record.all()

        if not master_records.exists():
            messages.append(
                (
                    f"[{check.id}]:Accommodation with id={accommodation.id} marked "
                    "with is_principal=False but is missing a AccommodationMasterRecord"
                ),
            )

            return messages

        for master_record in master_records:
            # get principal accommodation off the master record
            principal_accommodation = MvAccommodation.objects.filter(
                id=master_record.principal_record_id
            ).first()

            if not principal_accommodation:
                messages.append(
                    (
                        f"[{check.id}]: AccommodationMasterRecord with id="
                        f"{master_record.record_id} has no principal accommodation"
                    ),
                )

                return messages

            # Suitable checks are linked to both AR and Accommodations.
            # We know exactly which AR we need to use here.
            accommodation_request = check.AR.first()

            if not accommodation_request:
                messages.append(
                    (
                        f"[{check.id}]: Escalation not raised. Check with id={check.id}"
                        " is not attached to any ARs"
                    ),
                )

                return messages

            pricipal_has_check = principal_accommodation.checks.filter(
                check_type=check.check_type,
                AR__id=accommodation_request.id,
            )

            if pricipal_has_check.exists():
                messages.append(
                    (
                        f"[{check.id}]: Principal accommodation with id="
                        f"{principal_accommodation.id} already has a check of "
                        "this type, not duplicating"
                    ),
                )

                return messages

            # duplicate the check
            new_check = deepcopy(check)
            new_check.id = uuid.uuid4()
            new_check.save()

            new_check.accommodation.set([principal_accommodation])
            new_check.AR.add(accommodation_request)
            messages.append(
                (
                    f"[{check.id}]: Created new check with id={new_check.id} "
                    "linked to principal accommodation with "
                    f"id={principal_accommodation.id} "
                    f"of duplicate sponsor with id={accommodation.id}"
                ),
            )

            # if appropriate, also create an escalation for this check
            if new_check.check_status == DevCheckV2.CheckStatus.FAILED:
                messages.append(
                    (
                        f"[{check.id}]: Creating escalation for new failed check "
                        f"with id={new_check.id}"
                    ),
                )

                notification_data = NotificationData(
                    alert_type=SafeguardingNotification.AlertType.SAFEGUARDING_CHECK,
                    check=new_check,
                    accommodation=principal_accommodation,
                )

                loop_and_raise(accommodation_request, notification_data)

                messages.append(
                    (
                        f"[{check.id}]: Escalation handled for new failed check "
                        f"with id={new_check.id} linked against principal accommodation"
                        f" with id={principal_accommodation.id}"
                    ),
                )

            messages.append(
                f"[{check.id}]: End - Solving check on duplicate record",
            )

    return messages


def process_update_guest_titles(guest: MvPerson) -> bool:
    correct_title = guest.get_full_name()

    if correct_title == guest.title:
        return False
    else:
        guest.title = correct_title
        guest.save()
        return True
