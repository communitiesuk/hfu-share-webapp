from datetime import datetime, timezone

from bs4 import BeautifulSoup
from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import ReassignmentRequest
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvUkPostcodeFactory,
    ReassignmentRequestFactory,
)
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from user_management.tests.base import get_admin_user, get_la_user


class UnassignedAccommodationRequestListViewTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def setUp(self):
        super().setUp()

        self.postcode_one = MvUkPostcodeFactory(postcode="AA1 1AA")
        self.accom_one = MvAccommodationFactory(
            full_address="Number 1 road", postcode=self.postcode_one
        )

        self.ar_one = AccReqFactory(
            title="Test One",
            accommodation_id=[self.accom_one.id],
            latest_application_date=datetime(2029, 1, 1, tzinfo=timezone.utc),
        )

        self.ar_two = AccReqFactory(
            title="Test Two",
            ltla_name=["some_ltla"],
        )

        self.accom_three = MvAccommodationFactory(full_address="Number 3 road")

        self.ar_three = AccReqFactory(
            title="Test Three",
            accommodation_id=[self.accom_three.id],
            latest_application_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )

        self.rr_three = ReassignmentRequestFactory(
            accommodation_request=self.ar_three,
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            destination_ltla_name="some ltla",
            created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )

        self.postcode_four = MvUkPostcodeFactory(postcode="DD4 4DD")
        self.accom_four = MvAccommodationFactory(
            full_address="Number 4 road", postcode=self.postcode_four
        )
        self.ar_four = AccReqFactory(
            title="Test Four", accommodation_id=[self.accom_four.id]
        )
        self.rr_four = ReassignmentRequestFactory(
            accommodation_request=self.ar_four,
            outcome=ReassignmentRequest.Outcome.PENDING,
            destination_ltla_name="some ltla",
        )

        self.postcode_five = MvUkPostcodeFactory(postcode="EE5 5EE")
        self.accom_five = MvAccommodationFactory(
            full_address="Number 5 road", postcode=self.postcode_five
        )
        self.ar_five = AccReqFactory(
            title="Test five",
            accommodation_id=[self.accom_five.id],
            latest_application_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        self.rr_five = ReassignmentRequestFactory(
            accommodation_request=self.ar_five,
            outcome=ReassignmentRequest.Outcome.REJECTED,
            destination_ltla_name="some ltla",
        )

        self.postcode_six = MvUkPostcodeFactory(postcode="FF6 6FF")
        self.accom_six = MvAccommodationFactory(
            full_address="Number 6 road", postcode=self.postcode_six
        )
        self.ar_six = AccReqFactory(
            title="Test six",
            accommodation_id=[self.accom_six.id],
            latest_application_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        self.rr_six = ReassignmentRequestFactory(
            accommodation_request=self.ar_six,
            outcome=ReassignmentRequest.Outcome.REJECTED,
            destination_ltla_name="some ltla",
        )

        self.postcode_seven = MvUkPostcodeFactory(postcode="GG7 7GG")
        self.accom_seven = MvAccommodationFactory(
            full_address="Number 7 road", postcode=self.postcode_seven
        )
        self.ar_seven = AccReqFactory(
            title="Test seven",
            accommodation_id=[self.accom_seven.id],
            latest_application_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        self.rr_seven_1 = ReassignmentRequestFactory(
            accommodation_request=self.ar_seven,
            outcome=ReassignmentRequest.Outcome.REJECTED,
            destination_ltla_name="some ltla",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        self.rr_seven_2 = ReassignmentRequestFactory(
            accommodation_request=self.ar_seven,
            outcome=ReassignmentRequest.Outcome.REJECTED,
            destination_ltla_name="some ltla",
            created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        self.rr_seven_3 = ReassignmentRequestFactory(
            accommodation_request=self.ar_seven,
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            destination_ltla_name="some ltla",
            created_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        )

        self.ar_eight = AccReqFactory(
            title="Test Eight",
        )

    def test_ar_ordering(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "unassigned-accommodation-requests:unassigned-accommodation-requests",
            )
        )

        html = response.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table", class_="govuk-table")
        tbody = table.find("tbody")
        rows = tbody.find_all("tr")

        self.assertTrue(self.ar_six.title in str(rows[0]))
        self.assertTrue(self.ar_five.title in str(rows[1]))
        self.assertTrue(self.ar_four.title in str(rows[2]))
        self.assertTrue(self.ar_three.title in str(rows[3]))
        self.assertTrue(self.ar_seven.title in str(rows[4]))
        self.assertTrue(self.ar_one.title in str(rows[5]))
        self.assertTrue(self.ar_two.title not in str(tbody))

    def test_no_access_to_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "unassigned-accommodation-requests:unassigned-accommodation-requests",
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_list_view_table_displays_data(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "unassigned-accommodation-requests:unassigned-accommodation-requests",
            )
        )

        html = response.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table", class_="govuk-table")
        tbody = table.find("tbody")
        rows = tbody.find_all("tr")

        self.assertTrue(self.ar_six.title in str(rows[0]))
        self.assertTrue(self.postcode_six.postcode in str(rows[0]))
        self.assertTrue(self.accom_six.full_address in str(rows[0]))
        self.assertTrue(self.rr_six.destination_ltla_name in str(rows[0]))
        self.assertTrue("Rejected" in str(rows[0]))
