from pathlib import Path

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, QuerySet

from accounts.enums import BROWSER_TEST_LTLA_NAMES
from deduplication.models import (
    AccommodationDuplicateGroup,
    GuestDuplicateGroup,
    SponsorDuplicateGroup,
)
from ontology.models import (
    Comment,
    CommentAttachment,
    DevCheckV2,
    ExportToolObject,
    HiddenUnassignedAccommodationRequest,
    MvAccommodation,
    MvAccommodationRequest,
    MvGroup,
    MvInteraction,
    MvInteractionAttachmentMetadata,
    MvPerson,
    MvUkPostcode,
    MvVolunteer,
    PersonMasterRecord,
    ReassignmentRequest,
    SafeguardingNotification,
    SafeguardingReferral,
    SponsorMasterRecord,
    SponsorshipCertificationForm,
    VisaApplication,
    VisaInformationRequest,
    VisaInformationRequestComments,
)
from ontology.models.AccommodationMasterRecord import AccommodationMasterRecord
from ontology.models.SponsorshipCertificationAttachmentMetadata import (
    SponsorshipCertificationAttachmentMetadata,
)

BROWSER_TEST_ID_PREFIX = "browser-test"
BROWSER_TEST_LTLA_NAME = BROWSER_TEST_LTLA_NAMES[0]
SEED_DATA_DIR = Path(__file__).resolve().parent / "data"
PREFIXED = Q(pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-")


def collect_browser_test_records() -> list[tuple[str, QuerySet]]:
    name = BROWSER_TEST_LTLA_NAME

    ars = MvAccommodationRequest._base_manager.filter(
        Q(ltla_name__overlap=[name]) | PREFIXED
    )
    ar_ids = list(ars.values_list("id", flat=True))
    person_ids = [pid for ar in ars for pid in (ar.person_id or [])]
    sponsor_ids = [sid for ar in ars for sid in (ar.sponsor_id or [])]
    accommodation_ids = [aid for ar in ars for aid in (ar.accommodation_id or [])]
    group_ids = list(
        ars.exclude(group__isnull=True).values_list("group__id", flat=True)
    )
    uam_refs = [
        ref for ar in ars for ref in (ar.sponsorship_certification_number_id or [])
    ]
    uam_refs += list(
        SponsorshipCertificationForm._base_manager.filter(
            Q(ltla_name__overlap=[name]) | PREFIXED
        ).values_list("reference", flat=True)
    )

    reassignments = ReassignmentRequest._base_manager.filter(
        Q(source_ltla_name__overlap=[name]) | Q(destination_ltla_name=name) | PREFIXED
    )
    reassignment_ids = list(reassignments.values_list("pk", flat=True))

    guest_dup_groups = GuestDuplicateGroup._base_manager.filter(
        Q(guests__id__in=person_ids)
        | Q(guests__id__startswith=f"{BROWSER_TEST_ID_PREFIX}-")
    ).distinct()
    person_ids += list(
        guest_dup_groups.exclude(principal_record__isnull=True).values_list(
            "principal_record__id", flat=True
        )
    )
    sponsor_dup_groups = SponsorDuplicateGroup._base_manager.filter(
        Q(sponsors__id__in=sponsor_ids)
        | Q(sponsors__id__startswith=f"{BROWSER_TEST_ID_PREFIX}-")
    ).distinct()
    sponsor_ids += list(
        sponsor_dup_groups.exclude(principal_record__isnull=True).values_list(
            "principal_record__id", flat=True
        )
    )
    accommodation_dup_groups = AccommodationDuplicateGroup._base_manager.filter(
        Q(accommodations__id__in=accommodation_ids)
        | Q(accommodations__id__startswith=f"{BROWSER_TEST_ID_PREFIX}-")
    ).distinct()
    accommodation_ids += list(
        accommodation_dup_groups.exclude(principal_record__isnull=True).values_list(
            "principal_record__id", flat=True
        )
    )

    virs = VisaInformationRequest._base_manager.filter(
        Q(ltla_name=name) | Q(visa_application__ltla_name=name) | PREFIXED
    )

    interactions = MvInteraction._base_manager.filter(
        Q(linked_accommodation_request__id__in=ar_ids)
        | Q(linked_guest__id__in=person_ids)
        | Q(linked_sponsor__id__in=sponsor_ids)
        | Q(linked_accommodation__id__in=accommodation_ids)
    ).distinct()
    interaction_ids = [str(pk) for pk in interactions.values_list("pk", flat=True)]

    comments = Comment._base_manager.filter(
        Q(attached_accommodation_request_id__id__in=ar_ids)
        | Q(attached_reassignment_request_id__id__in=reassignment_ids)
        | PREFIXED
    ).distinct()
    comment_ids = list(comments.values_list("pk", flat=True))

    rid_values = [f"{ref}-uk" for ref in uam_refs] + [f"{ref}-ukr" for ref in uam_refs]

    accommodations = MvAccommodation._base_manager.filter(
        Q(id__in=accommodation_ids) | PREFIXED
    )
    postcode_ids = list(accommodations.values_list("postcode_id", flat=True))

    return [
        (
            "safeguarding notifications",
            SafeguardingNotification._base_manager.filter(
                Q(ar__id__in=ar_ids)
                | Q(applicant_person_ids__overlap=person_ids or ["-"])
            ).distinct(),
        ),
        (
            "safeguarding referrals",
            SafeguardingReferral._base_manager.filter(person__id__in=person_ids),
        ),
        (
            "visa information request comments",
            VisaInformationRequestComments._base_manager.filter(
                Q(visa_information_request__in=virs) | PREFIXED
            ),
        ),
        ("visa information requests", virs),
        (
            "comment attachments",
            CommentAttachment._base_manager.filter(comment__id__in=comment_ids),
        ),
        ("comments", comments),
        (
            "interaction attachment metadata",
            MvInteractionAttachmentMetadata._base_manager.filter(
                rid__in=interaction_ids
            ),
        ),
        ("interactions", interactions),
        (
            "hidden unassigned accommodation requests",
            HiddenUnassignedAccommodationRequest._base_manager.filter(
                accommodation_request__id__in=ar_ids
            ),
        ),
        ("reassignment requests", reassignments),
        ("guest duplicate groups", guest_dup_groups),
        ("sponsor duplicate groups", sponsor_dup_groups),
        ("accommodation duplicate groups", accommodation_dup_groups),
        (
            "checks",
            DevCheckV2._base_manager.filter(
                PREFIXED
                | Q(AR__id__in=ar_ids)
                | Q(person__id__in=person_ids)
                | Q(sponsor__id__in=sponsor_ids)
                | Q(accommodation__id__in=accommodation_ids)
                | Q(group__id__in=group_ids)
            ).distinct(),
        ),
        (
            "person master records",
            PersonMasterRecord._base_manager.filter(
                Q(principal_record__id__in=person_ids) | Q(persons__id__in=person_ids)
            ).distinct(),
        ),
        (
            "sponsor master records",
            SponsorMasterRecord._base_manager.filter(
                Q(principal_record__id__in=sponsor_ids)
                | Q(sponsors__id__in=sponsor_ids)
            ).distinct(),
        ),
        (
            "accommodation master records",
            AccommodationMasterRecord._base_manager.filter(
                Q(principal_record__id__in=accommodation_ids)
                | Q(accommodations__id__in=accommodation_ids)
            ).distinct(),
        ),
        (
            "uam attachment metadata",
            SponsorshipCertificationAttachmentMetadata._base_manager.filter(
                Q(rid__in=rid_values)
                | Q(sponsorship_certification_form__reference__in=uam_refs)
                | Q(id__startswith=BROWSER_TEST_ID_PREFIX)
            ),
        ),
        (
            "uam forms",
            SponsorshipCertificationForm._base_manager.filter(
                Q(reference__in=uam_refs) | PREFIXED
            ),
        ),
        (
            "visa applications",
            VisaApplication._base_manager.filter(Q(ltla_name=name) | PREFIXED),
        ),
        (
            "export tool objects",
            ExportToolObject._base_manager.filter(
                Q(ltla_name__overlap=[name]) | PREFIXED
            ),
        ),
        ("people", MvPerson._base_manager.filter(Q(id__in=person_ids) | PREFIXED)),
        ("accommodation requests", ars),
        ("groups", MvGroup._base_manager.filter(Q(id__in=group_ids) | PREFIXED)),
        (
            "sponsors",
            MvVolunteer._base_manager.filter(Q(id__in=sponsor_ids) | PREFIXED),
        ),
        ("accommodations", accommodations),
        (
            "postcodes",
            MvUkPostcode._base_manager.filter(
                Q(ltla_name=name) | Q(pk__in=postcode_ids) | PREFIXED
            ),
        ),
    ]


def _delete_with_audit_logs(label: str, queryset: QuerySet) -> None:
    model = queryset.model
    pks = [str(pk) for pk in queryset.values_list("pk", flat=True)]
    if not pks:
        return
    queryset.delete()
    LogEntry.objects.filter(
        content_type=ContentType.objects.get_for_model(model),
        object_pk__in=pks,
    ).delete()
    print(f"wiped {len(pks)} {label}")


def wipe_browser_test_la_data() -> None:
    for label, queryset in collect_browser_test_records():
        _delete_with_audit_logs(label, queryset)

    stray_logs = LogEntry.objects.filter(
        object_pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-"
    )
    stray_log_count = stray_logs.count()
    if stray_log_count:
        stray_logs.delete()
        print(f"wiped {stray_log_count} stray audit log entries")
