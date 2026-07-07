import os
import random

from faker import Faker

from accommodation_requests.forms import (
    AccommodationRequestUpdateSafeguardingChecksForm,
)
from accounts.models import User
from hfurb_scripts.seeders.helpers import get_group_info_from_ltla
from ontology.models import (
    DevCheckV2,
    MvAccommodationRequest,
    ReassignmentRequest,
)
from ontology.models.CheckType import CheckType
from ontology.models.MvInteraction import MvInteraction
from ontology.tests.factories import (
    DevCheckV2Factory,
    InteractionFactory,
)

fake = Faker()


def mutate_closed_left_programme(accommodation_request: MvAccommodationRequest) -> None:
    InteractionFactory(
        id=f"interaction-{fake.uuid4()}",
        interaction_contact=MvInteraction.InteractionContact.LEAVING_PROGRAMME,
        interaction_type="Return to Ukraine",
        linked_accommodation_request=accommodation_request,
        interaction_notes="Interaction notes for leaving programme.",
        title=MvInteraction.InteractionContact.LEAVING_PROGRAMME,
    )


def mutate_rematch_required(accommodation_request: MvAccommodationRequest) -> None:
    # Create RR
    ltla_name = random.choice(["Lewisham", "Bromley", "Croydon"])
    # Ensure ltla_name is different from the current one
    if ltla_name == accommodation_request.ltla_name:
        ltla_name = "Bromley" if ltla_name != "Bromley" else "Lewisham"

    destination = get_group_info_from_ltla(ltla_name)

    reassignment_request = ReassignmentRequest(
        id=f"rr-{fake.uuid4()}",
        accommodation_request=accommodation_request,
        outcome=ReassignmentRequest.Outcome.PENDING,
        reason="Reason for rematch required",
        proposed_by_country="England",
        accommodation_request_title=accommodation_request.title,
        destination_country=destination.da_name,  # type: ignore[union-attr]
        destination_ltla_name=destination.ltla_name,  # type: ignore[union-attr]
        destination_utla_code=destination.utla_gss_code,  # type: ignore[union-attr]
        destination_utla_name=destination.utla_name,  # type: ignore[union-attr]
        source_ltla_name=accommodation_request.ltla_name,
        source_utla_name=accommodation_request.utla_name,
    )
    reassignment_request.save()

    reassignment_request.guests.set(accommodation_request.get_people())

    # randomise number from 0 to 2
    random_number = random.randint(0, 2)
    should_approve = random_number == 0
    if not should_approve:
        return  # Do not approve the request

    # Approve RR
    reassignment_request.outcome = ReassignmentRequest.Outcome.ACCEPTED
    reassignment_request.save()

    InteractionFactory(
        id=f"interaction-{fake.uuid4()}",
        interaction_contact=MvInteraction.InteractionContact.REMATCH_REQUIRED,
        interaction_type="Rematch Required",
        linked_accommodation_request=accommodation_request,
        interaction_notes="Interaction notes for rematch required.",
        title=MvInteraction.InteractionContact.REMATCH_REQUIRED,
    )

    accommodation_request.ltla_name = [reassignment_request.destination_ltla_name]
    accommodation_request.utla_name = [reassignment_request.destination_utla_name]
    accommodation_request.checks_status = (
        MvAccommodationRequest.ChecksStatus.REMATCH_REQUIRED
    )

    accommodation_request.save()

    email = os.environ.get("ADMIN_EMAIL")
    author = User.objects.get(email=email)

    # Update AR accommodations
    accommodation_request.update_accommodation(new_accommodation=None, author=author)

    # Unlink hosts from AR
    accommodation_request.unlink_host(author=author)


def mutate_checks(  # noqa: C901
    accommodation_request: MvAccommodationRequest,
) -> None:
    checks = [
        (
            CheckType.Id.ACCOMM_SUITABLE,
            "accommodation",
            accommodation_request.primary_accommodation,
        ),
        (
            CheckType.Id.ACCOMM_EXISTS,
            "accommodation",
            accommodation_request.primary_accommodation,
        ),
        (
            CheckType.Id.SPONSOR_DBS,
            "sponsor",
            accommodation_request.primary_sponsor,
        ),
        (
            CheckType.Id.GROUP_ARRIVED,
            "group",
            accommodation_request.group,
        ),
    ]
    status = accommodation_request.checks_status

    def _create_check(type_id, link_attr, link_obj, check_status):
        check_type = CheckType.objects.get(id=type_id)
        devcheck = DevCheckV2Factory.build(
            check_type=check_type,
            check_status=check_status,
        )
        getattr(devcheck, link_attr).add(link_obj)
        if hasattr(devcheck, "AR"):
            devcheck.AR.add(accommodation_request)
        if check_status == DevCheckV2.CheckStatus.FAILED:
            devcheck.check_subtype = _get_reason(devcheck)
        devcheck.save()
        return devcheck

    def _get_reason(devcheck):
        choices = []
        if devcheck.check_type.id == CheckType.Id.ACCOMM_EXISTS:
            choices = [
                DevCheckV2.AccommExistsFailureReason.NOT_RESIDENTIAL,
                DevCheckV2.AccommExistsFailureReason.DOES_NOT_EXIST,
            ]

        if devcheck.check_type.id == CheckType.Id.ACCOMM_SUITABLE:
            choices = [
                DevCheckV2.SuitabilityFailure.OVERCROWDED,
                DevCheckV2.SuitabilityFailure.NOT_ENOUGH_SPACE,
                DevCheckV2.SuitabilityFailure.POOR_CONDITION,
                DevCheckV2.SuitabilityFailure.UNSUITABLE_FACILITIES,
                DevCheckV2.SuitabilityFailure.NO_CONSENT_TO_LIVE_AT_ADDRESS,
                DevCheckV2.SuitabilityFailure.SPONSOR_NOT_LINKED_TO_ADDRESS,
                DevCheckV2.SuitabilityFailure.SPONSOR_DOES_NOT_LIVE_AT_ADDRESS,  # noqa: E501
            ]

        if devcheck.check_type.id == CheckType.Id.SPONSOR_DBS:
            choices = [
                DevCheckV2.SponsorDBSFailureReason.DBS_CHECK_FAILED,
                DevCheckV2.SponsorDBSFailureReason.NO_CONSENT_TO_BE_SPONSOR,
                DevCheckV2.SponsorDBSFailureReason.NO_RESPONSE,
                DevCheckV2.SponsorDBSFailureReason.SPONSOR_NOT_SUITABLE,
            ]

        if choices:
            return random.choice(choices)

        return None

    if status == MvAccommodationRequest.ChecksStatus.CHECKS_PARTIALLY_COMPLETED:
        type_id, link_attr, link_obj = random.choice(checks)
        _create_check(type_id, link_attr, link_obj, DevCheckV2.CheckStatus.PASSED)

    elif status == MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED:
        for type_id, link_attr, link_obj in checks:
            _create_check(type_id, link_attr, link_obj, DevCheckV2.CheckStatus.PASSED)

    elif status == MvAccommodationRequest.ChecksStatus.SOME_CHECKS_FAILED:
        type_id, link_attr, link_obj = random.choice(checks)
        devcheck = _create_check(
            type_id, link_attr, link_obj, DevCheckV2.CheckStatus.FAILED
        )

        # create escalated check
        if link_attr in ["accommodation", "sponsor"]:
            form_data = {
                "check_type": devcheck.check_type,
                "status": DevCheckV2.CheckStatus.FAILED,
            }

            if link_attr == "accommodation":
                form_data["accommodations"] = link_obj.pk
                form_data["accommodation_exists_failure"] = _get_reason(devcheck)
                form_data["accommodation_suitable_failure"] = _get_reason(devcheck)
            elif link_attr == "sponsor":
                form_data["sponsors"] = link_obj.pk
                form_data["sponsor_dbs_failure"] = _get_reason(devcheck)

            email = os.environ.get("ADMIN_EMAIL")
            user = User.objects.get(email=email)

            form = AccommodationRequestUpdateSafeguardingChecksForm(
                data=form_data,
                instance=accommodation_request,
                user=user,
                dev_check_v2_id=devcheck.id,
            )
            form.is_valid()
            form.save()
