import logging
import time

from django.db.models import Q
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from accounts.models import User
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MvPerson)
@receiver(post_save, sender=MvAccommodation)
def post_edit_update_accommodation_request_title(sender, instance, **kwargs):
    if isinstance(instance, MvPerson):
        _handle_person_update(instance)
    elif isinstance(instance, MvAccommodation):
        _handle_accommodation_update(instance)


def _handle_person_update(person: MvPerson):
    requests = set(
        MvAccommodationRequest.objects.filter(person_id__contains=[person.id])
    )
    if person.get_accommodation_request():
        requests.add(person.accommodation_request)

    for req in requests:
        if req.is_primary_contact(person):
            req.update_primary_contact(person)


def _handle_accommodation_update(accommodation: MvAccommodation):
    for req in MvAccommodationRequest.objects.filter(
        primary_accommodation_id=accommodation.id
    ):
        req.update_title()


def update_ar_checks_status_for_ar_ids(ar_ids, author=None, devcheck_instance=None):
    if not ar_ids:
        return

    if author is None and devcheck_instance is not None:
        author_id = getattr(devcheck_instance, "create_by", None)
        if isinstance(author_id, int):
            author = User.objects.filter(id=devcheck_instance.create_by).first()

    accommodation_requests_to_update = MvAccommodationRequest.objects.filter(
        id__in=ar_ids,
    ).exclude(
        checks_status__in=[
            MvAccommodationRequest.ChecksStatus.CLOSED_DUPLICATE,
            MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
            MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            MvAccommodationRequest.ChecksStatus.CANCELLED,
        ]
    )

    dev_check_id = devcheck_instance.id if devcheck_instance is not None else "N/A"
    dev_check_type_id = (
        devcheck_instance.check_type.id
        if devcheck_instance is not None and devcheck_instance.check_type is not None
        else "N/A"
    )

    loop_start_time = time.time_ns()
    logger.info(
        (
            "Started update_ar_checks_status_for_ar_ids looping for "
            "ar_ids=%s, check_id=%s, check_type_id=%s"
        ),
        ar_ids,
        dev_check_id,
        dev_check_type_id,
    )

    for ar in accommodation_requests_to_update:
        start_time = time.time_ns()
        logger.info(
            (
                "Started calling determine_checks_status_from_linked_objects for "
                "ar_id=%s, check_id=%s, check_type_id=%s"
            ),
            ar.id,
            dev_check_id,
            dev_check_type_id,
        )

        new_status = ar.determine_checks_status_from_linked_objects()

        processing_time = time.time_ns() - start_time

        logger.info(
            (
                "Finished calling determine_checks_status_from_linked_objects for"
                "ar_id=%s, check_id=%s, check_type_id=%s took %.6f seconds."
            ),
            ar.id,
            dev_check_id,
            dev_check_type_id,
            processing_time / 1e9,
        )

        if ar.checks_status != new_status:
            ar.update_checks_status(new_status, author)

    loop_processing_time = time.time_ns() - loop_start_time

    logger.info(
        (
            "Finished update_ar_checks_status_for_ar_ids looping for "
            "ar_ids=%s, check_id=%s, check_type_id=%s took %.6f seconds."
        ),
        ar_ids,
        dev_check_id,
        dev_check_type_id,
        loop_processing_time / 1e9,
    )


@receiver(m2m_changed, sender=DevCheckV2.accommodation.through)
def devcheckv2_accommodation_changed(sender, instance, action, pk_set, **kwargs):
    instance_id = instance.id if instance is not None else "N/A"
    instance_check_type_id = (
        instance.check_type.id
        if instance is not None and instance.check_type is not None
        else "N/A"
    )

    logger.info(
        "m2m_changed action=%s, id=%s, pk_set=%s, check_type_id=%s",
        action,
        instance_id,
        pk_set,
        instance_check_type_id,
    )

    if action in ["post_remove", "post_clear"]:
        if instance.check_type.id == CheckType.Id.ACCOMM_EXISTS:
            ar_ids = set(
                MvAccommodationRequest.objects.filter(
                    Q(primary_accommodation_id__in=list(pk_set))
                    | Q(accommodation_id__overlap=list(pk_set))
                    | Q(bridging_accommodation_id__in=list(pk_set))
                    | Q(temporary_accommodation_id__in=list(pk_set))
                ).values_list("id", flat=True)
            )

            update_ar_checks_status_for_ar_ids(ar_ids, devcheck_instance=instance)


@receiver(m2m_changed, sender=DevCheckV2.sponsor.through)
def devcheckv2_sponsor_changed(sender, instance, action, pk_set, **kwargs):
    instance_id = instance.id if instance is not None else "N/A"
    instance_check_type_id = (
        instance.check_type.id
        if instance is not None and instance.check_type is not None
        else "N/A"
    )

    logger.info(
        "m2m_changed action=%s, id=%s, pk_set=%s, check_type_id=%s",
        action,
        instance_id,
        pk_set,
        instance_check_type_id,
    )

    if action in ["post_remove", "post_clear"]:
        ar_ids = set(
            MvAccommodationRequest.objects.filter(
                Q(sponsor_id__overlap=list(pk_set))
                | Q(active_host_id__in=list(pk_set))
                | Q(primary_sponsor_id__in=list(pk_set))
            )
            .exclude(sponsor_withdrawn__contains=list(pk_set))
            .values_list("id", flat=True)
        )
        update_ar_checks_status_for_ar_ids(ar_ids, devcheck_instance=instance)


def handle_devcheckv2_change(sender, instance: DevCheckV2, **kwargs):
    instance_id = instance.id if instance is not None else "N/A"
    instance_check_type_id = (
        instance.check_type.id
        if instance is not None and instance.check_type is not None
        else "N/A"
    )

    logger.info(
        "check_changed id=%s, check_type_id=%s",
        instance_id,
        instance_check_type_id,
    )

    ar_ids = instance.get_related_ar_ids()
    update_ar_checks_status_for_ar_ids(ar_ids, devcheck_instance=instance)


post_save.connect(handle_devcheckv2_change, sender=DevCheckV2)
post_delete.connect(handle_devcheckv2_change, sender=DevCheckV2)
