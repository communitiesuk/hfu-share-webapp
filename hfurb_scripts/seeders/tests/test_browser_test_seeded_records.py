from django.test import override_settings

from accounts.tests.factories import UserFactory
from browser_tests.seeded_data import SeededAccommodationRequest, SeededGuest
from browser_tests.tests.test_guest_deduplication import (
    GUEST_ARRIVED_VISA_CHECKS_REQUIRED,
    GUEST_CONFIRMED_VISA_CHECKS_REQUIRED,
)
from browser_tests.tests.test_safeguarding import (
    AR_CHECKS_PARTIALLY_COMPLETED_WITH_CASE_COMMENTS,
    AR_CHECKS_REQUIRED_THREE_GUESTS,
    AR_CHECKS_REQUIRED_TWO_GUESTS,
    AR_DEDUPLICATED_GUEST_PAIR,
    AR_REJECTED_OUTBOUND_REASSIGNMENT,
)
from hfurb_scripts.seeders.stages.seed_browser_test_la import seed_browser_test_la
from hfurb_scripts.seeders.tests.helpers import create_browser_test_la_groups
from ontology.models import MvAccommodationRequest, MvPerson
from test_utils.base import BaseTestCase


@override_settings(ENVIRONMENT="dev")
class BrowserTestSeededRecordsTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        groups = create_browser_test_la_groups()
        UserFactory().groups.add(groups[0])
        seed_browser_test_la()

    def assert_seeded_guest(self, expected: SeededGuest) -> None:
        person = MvPerson.objects.get(id=expected.id)
        self.assertEqual(f"{person.first_name} {person.last_name}", expected.full_name)
        self.assertEqual(
            person.date_of_birth.strftime("%-d %B %Y"), expected.date_of_birth
        )
        self.assertIn(expected.email, person.email)
        self.assertIn(expected.phone, person.phone)
        self.assertIn(expected.passport_id, person.passport_id)
        self.assertEqual(
            person.accommodation_request.title.replace("\n", " "),
            expected.accommodation_request_title,
        )

    def assert_seeded_accommodation_request(
        self, expected: SeededAccommodationRequest
    ) -> None:
        ar = MvAccommodationRequest.objects.get(id=expected.id)
        self.assertEqual(ar.group.title, expected.full_name)
        self.assertEqual(
            ar.title.replace("\n", " "), expected.accommodation_request_title
        )
        self.assertEqual(
            ar.primary_accommodation.full_address.replace("\n", " "),
            expected.address,
        )
        sponsor = ar.primary_sponsor
        self.assertEqual(f"{sponsor.full_name} ({sponsor.email})", expected.sponsor)

    def test_accommodation_requests_the_safeguarding_journeys_rely_on_are_seeded(
        self,
    ):
        for expected in (
            AR_CHECKS_REQUIRED_THREE_GUESTS,
            AR_CHECKS_REQUIRED_TWO_GUESTS,
            AR_REJECTED_OUTBOUND_REASSIGNMENT,
            AR_CHECKS_PARTIALLY_COMPLETED_WITH_CASE_COMMENTS,
            AR_DEDUPLICATED_GUEST_PAIR,
        ):
            with self.subTest(expected.full_name):
                self.assert_seeded_accommodation_request(expected)

    def test_guests_the_dedupe_journey_relies_on_are_seeded(self):
        for expected in (
            GUEST_CONFIRMED_VISA_CHECKS_REQUIRED,
            GUEST_ARRIVED_VISA_CHECKS_REQUIRED,
        ):
            with self.subTest(expected.full_name):
                self.assert_seeded_guest(expected)
