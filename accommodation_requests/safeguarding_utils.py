import logging
import uuid
from dataclasses import dataclass
from typing import List, Optional

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from case_management.settings import sentry_sdk
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvVolunteer,
    SafeguardingNotification,
    SafeguardingReferral,
)

logger = logging.getLogger(__name__)


@dataclass
class NotificationData:
    alert_type: Optional[str] = None
    check: Optional[DevCheckV2] = None
    title: Optional[str] = None
    description: Optional[str] = None
    sponsor: Optional[MvVolunteer] = None
    accommodation: Optional[MvAccommodation] = None


def bulk_create_escalations(people_list: List) -> None:
    if not people_list:
        return

    principal_people = [p for p in people_list if p.is_principal is not False]
    if not principal_people:
        return

    current_time = timezone.now()
    unique_people = list({person.id: person for person in principal_people}.values())
    person_ids = [person.id for person in unique_people]

    existing_referrals = (
        SafeguardingReferral.objects.select_for_update()
        .filter(person_id__in=person_ids)
        .values("person_id", "alerted_status")
    )

    existing_lookup = {
        ref["person_id"]: ref["alerted_status"] for ref in existing_referrals
    }

    new_referrals = []
    alerted_to_update = []
    other_to_update = []

    for person in unique_people:
        if person.id not in existing_lookup:
            new_referrals.append(
                SafeguardingReferral(
                    id=f"safeguarding_referral-{str(uuid.uuid4())}",
                    person_id=person.id,
                    created_at=current_time,
                    alerted_status=SafeguardingReferral.AlertedStatus.NOT_ALERTED,
                )
            )
        else:
            # Queue for update based on current status
            current_status = existing_lookup[person.id]
            if current_status == SafeguardingReferral.AlertedStatus.ALERTED:
                alerted_to_update.append(person.id)
            else:
                other_to_update.append(person.id)

    # Execute bulk operations
    if new_referrals:
        SafeguardingReferral.objects.bulk_create(new_referrals)

    if alerted_to_update:
        SafeguardingReferral.objects.filter(person_id__in=alerted_to_update).update(
            alerted_status=SafeguardingReferral.AlertedStatus.SOME_ALERTED,
            modified_at=current_time,
        )

    if other_to_update:
        SafeguardingReferral.objects.filter(person_id__in=other_to_update).update(
            modified_at=current_time
        )


def raise_escalation(person):
    bulk_create_escalations([person])


def create_notification_params(
    accommodation_request, notification_data: NotificationData
) -> dict:
    params = {
        "ar": accommodation_request,
        "description": notification_data.description
        or (
            notification_data.check.get_check_subtype_label()
            if notification_data.check
            else None
        ),
        "alert_type": notification_data.alert_type,
        "name": notification_data.title
        or (
            notification_data.check.get_check_failed_title()
            if notification_data.check
            else None
        ),
        "alert_status": SafeguardingNotification.AlertStatus.ESCALATED,
        "new_alert_status": (
            SafeguardingNotification.NewAlertStatus.AUTO_ESCALATED_TO_UKVI
        ),
        "created_at": timezone.now(),
        "id": str(uuid.uuid4()),
        "dev_check_v2": notification_data.check if notification_data.check else None,
    }

    if notification_data.sponsor:
        params["sponsor_ids"] = [notification_data.sponsor.id]
        params["sponsor_names"] = [notification_data.sponsor.get_full_name()]
    if notification_data.accommodation:
        params["accommodation_ids"] = [notification_data.accommodation.id]
        full_address = notification_data.accommodation.full_address
        if full_address:
            params["full_addresses"] = [full_address]
        else:
            params["full_addresses"] = []

    return params


def bulk_create_notifications(ar_notification_pairs: List[tuple]) -> None:
    if not ar_notification_pairs:
        return

    notifications = []
    for accommodation_request, notification_data in ar_notification_pairs:
        params = create_notification_params(accommodation_request, notification_data)
        notifications.append(SafeguardingNotification(**params))

    SafeguardingNotification.objects.bulk_create(notifications)


def raise_notification(accommodation_request, notification_data: NotificationData):
    bulk_create_notifications([(accommodation_request, notification_data)])


def add_related_ars_and_people(
    related_ars, notification_data, ar_notification_pairs, all_people
):
    for ar in related_ars:
        ar_notification_pairs.append((ar, notification_data))
        all_people.extend(list(ar.get_people()))


@transaction.atomic
def loop_and_raise(instance, notification_data: NotificationData):
    # Collect all accommodation requests and people to process
    ar_notification_pairs = [(instance, notification_data)]
    all_people = list(instance.get_people())

    # Handle sponsor-related escalations
    if (
        notification_data.sponsor
        and notification_data.alert_type
        == SafeguardingNotification.AlertType.SAFEGUARDING_CHECK
    ):
        related_ars = MvAccommodationRequest.objects.filter(
            Q(primary_sponsor_id=notification_data.sponsor.id)
            | Q(sponsor_id__contains=[notification_data.sponsor.id])
        ).exclude(id=instance.id)
        add_related_ars_and_people(
            related_ars, notification_data, ar_notification_pairs, all_people
        )

    # Handle accommodation-related escalations for ACCOMM_EXISTS checks
    if (
        notification_data.accommodation
        and notification_data.check
        and notification_data.check.check_type.id == CheckType.Id.ACCOMM_EXISTS
    ):
        related_ars = MvAccommodationRequest.objects.filter(
            Q(primary_accommodation_id=notification_data.accommodation.id)
            | Q(accommodation_id__contains=[notification_data.accommodation.id])
        ).exclude(id=instance.id)
        add_related_ars_and_people(
            related_ars, notification_data, ar_notification_pairs, all_people
        )

    bulk_create_notifications(ar_notification_pairs)
    bulk_create_escalations(all_people)


def recalculate_checks_status(
    accommodation_request_id: str,
    recalculate_closed: bool = False,
    author: str | None = None,
) -> str | None:
    with transaction.atomic():
        ar = MvAccommodationRequest.objects.select_for_update().get(
            id_=accommodation_request_id
        )

        try:
            new_status = ar.determine_checks_status_from_linked_objects(
                excluded_statuses=[]
                if recalculate_closed
                else MvAccommodationRequest.CLOSED_STATUSES
            )
            if ar.checks_status != new_status:
                ar.update_checks_status(new_status, author=author)
        except Exception:
            new_status = None
            logger.exception("Failed to recalculate checks status for AR %s", ar.id)
            sentry_sdk.capture_exception()

    return new_status
