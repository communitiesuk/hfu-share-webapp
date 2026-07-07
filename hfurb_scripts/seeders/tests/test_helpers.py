from django.test import TestCase

from accounts.enums import GroupType
from accounts.tests.factories import GroupInfoFactory
from hfurb_scripts.seeders.helpers import (
    build_complete_accommodation_scenario,
)
from ontology.models import (
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    VisaApplication,
)


class TestBuildCompleteAccommodationScenario(TestCase):
    def setUp(self):
        self.group_info = GroupInfoFactory(
            ltla_name="Test LTLA",
            utla_name="Test UTLA",
            group_type=GroupType.LOCAL_AUTHORITY,
        )

    def test_builds_complete_scenario_with_defaults(self):
        result = build_complete_accommodation_scenario(2, "Test LTLA")

        # Verify the accommodation request is created
        self.assertIsInstance(result, MvAccommodationRequest)
        self.assertEqual(result.number_of_people, 2)
        self.assertEqual(result.ltla_name, ["Test LTLA"])
        self.assertEqual(result.utla_name, ["Test UTLA"])

        # Verify default statuses are set
        self.assertEqual(
            result.status, MvAccommodationRequest.Status.ACCOMMODATION_ASSIGNED
        )
        self.assertEqual(
            result.checks_status, MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED
        )

    def test_builds_complete_scenario_with_custom_statuses(self):
        custom_visa_statuses = ["Arrived", "Issued", "Confirmed"]

        result = build_complete_accommodation_scenario(
            num_guests=3,
            ltla_name="Test LTLA",
            accommodation_type=(
                MvAccommodation.AccommodationType.TEMPORARY_ACCOMMODATION
            ),
            sponsor_type=MvVolunteer.SponsorType.LOCAL_AUTHORITY,
            upe_visa_status=MvPerson.UPEVisaStatus.WITHDRAWN,
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
            visa_statuses=custom_visa_statuses,
        )

        # Verify the accommodation request is created with custom parameters
        self.assertIsInstance(result, MvAccommodationRequest)
        self.assertEqual(result.number_of_people, 3)
        self.assertEqual(result.ltla_name, ["Test LTLA"])
        self.assertEqual(result.utla_name, ["Test UTLA"])

        # Verify custom statuses are set on accommodation request
        self.assertEqual(
            result.status, MvAccommodationRequest.Status.ACCOMMODATION_ASSIGNED
        )
        self.assertEqual(
            result.checks_status, MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED
        )

        # Verify accommodation has custom type
        accommodation = MvAccommodation.objects.get(id__in=result.accommodation_id)
        self.assertEqual(
            accommodation.accommodation_type,
            MvAccommodation.AccommodationType.TEMPORARY_ACCOMMODATION,
        )

        # Verify sponsor has custom type
        sponsor = result.primary_sponsor
        self.assertEqual(sponsor.sponsor_type, MvVolunteer.SponsorType.LOCAL_AUTHORITY)

        # Verify all persons have custom UPE visa status
        for i, person_id in enumerate(result.person_id):
            person = MvPerson.objects.get(id=person_id)
            self.assertEqual(person.upe_visa_status, MvPerson.UPEVisaStatus.WITHDRAWN)
            self.assertEqual(person.visa_status, custom_visa_statuses[i])

        # Verify visa applications have custom visa status
        visa_applications = VisaApplication.objects.filter(
            application_unique_application_number__in=result.unique_application_number
        )
        for i, visa_app in enumerate(visa_applications):
            self.assertEqual(visa_app.visa_status, custom_visa_statuses[i])
