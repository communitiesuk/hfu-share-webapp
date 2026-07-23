from datetime import datetime, timezone

from bs4 import BeautifulSoup
from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import ReassignmentRequest
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvUkPostcodeFactory,
    ReassignmentRequestFactory,
)
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from user_management.tests.base import get_admin_user, get_la_user


class UnassignedAccommodationRequestListViewTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.postcode_one = MvUkPostcodeFactory(
            postcode="AA11AA", postcode_formatted="AA1 1AA"
        )
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

        self.postcode_four = MvUkPostcodeFactory(
            postcode="DD44DD", postcode_formatted="DD4 4DD"
        )
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

        self.postcode_five = MvUkPostcodeFactory(
            postcode="EE55EE", postcode_formatted="EE5 5EE"
        )
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

        self.postcode_six = MvUkPostcodeFactory(
            postcode="FF66FF", postcode_formatted="FF6 6FF"
        )
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

        self.postcode_seven = MvUkPostcodeFactory(
            postcode="GG77GG", postcode_formatted="GG7 7GG"
        )
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

        self.client.force_login(get_admin_user())

    def get_page(self, query_string=""):
        url = reverse(
            "unassigned-accommodation-requests:unassigned-accommodation-requests"
        )
        return self.client.get(url + query_string)

    def get_displayed_titles(self, query_string=""):
        """Record titles in the order the table displays them."""
        response = self.get_page(query_string)
        return [record.title for record in response.context["table"].data]

    def get_table(self, query_string=""):
        html = self.get_page(query_string).content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("table", class_="govuk-table")

    def get_table_rows(self, query_string=""):
        return self.get_table(query_string).find("tbody").find_all("tr")

    def test_default_order_is_newest_application_date_first(self):
        titles = self.get_displayed_titles()

        self.assertEqual(
            titles,
            [
                "Test One",
                "Test Three",
                "Test six",
                "Test five",
                "Test seven",
                "Test Eight",
                "Test Four",
            ],
        )

    def test_records_assigned_to_a_local_authority_are_not_listed(self):
        self.assertNotIn("Test Two", self.get_displayed_titles())

    def test_sort_by_address_ascending(self):
        titles = self.get_displayed_titles("?sort=address")

        self.assertEqual(
            titles,
            [
                "Test One",
                "Test Three",
                "Test Four",
                "Test five",
                "Test six",
                "Test seven",
                "Test Eight",
            ],
        )

    def test_sort_by_address_descending(self):
        titles = self.get_displayed_titles("?sort=-address")

        self.assertEqual(
            titles,
            [
                "Test Eight",
                "Test seven",
                "Test six",
                "Test five",
                "Test Four",
                "Test Three",
                "Test One",
            ],
        )

    def test_sort_by_postcode_ascending(self):
        titles = self.get_displayed_titles("?sort=postcode")

        self.assertEqual(
            titles,
            [
                "Test One",
                "Test Four",
                "Test five",
                "Test six",
                "Test seven",
                "Test Eight",
                "Test Three",
            ],
        )

    def test_sort_by_postcode_descending(self):
        titles = self.get_displayed_titles("?sort=-postcode")

        self.assertEqual(
            titles,
            [
                "Test Three",
                "Test Eight",
                "Test seven",
                "Test six",
                "Test five",
                "Test Four",
                "Test One",
            ],
        )

    def test_local_authority_users_cannot_access_the_page(self):
        self.client.force_login(get_la_user())

        response = self.get_page()

        self.assertEqual(response.status_code, 404)

    def test_first_row_shows_name_address_postcode_and_hide_link(self):
        first_row = str(self.get_table_rows()[0])

        self.assertIn("Test One", first_row)
        self.assertIn("Number 1 road", first_row)
        self.assertIn("AA1 1AA", first_row)
        self.assertIn("Hide", first_row)

    def test_table_has_expected_column_headings(self):
        headings = str(self.get_table().find("thead"))

        self.assertIn("Name", headings)
        self.assertIn("Date of application", headings)
        self.assertIn("Address", headings)
        self.assertIn("Postcode", headings)
        self.assertNotIn("Reassignment", headings)

    def test_a_record_with_two_accommodations_lists_both_one_per_line(self):
        first = MvAccommodationFactory(
            full_address="Zebra house A",
            postcode=MvUkPostcodeFactory(
                postcode="ZZ88ZZ", postcode_formatted="ZZ8 8ZZ"
            ),
        )
        second = MvAccommodationFactory(
            full_address="Zebra house B",
            postcode=MvUkPostcodeFactory(
                postcode="ZZ99ZZ", postcode_formatted="ZZ9 9ZZ"
            ),
        )
        AccReqFactory(title="Test Multi", accommodation_id=[first.id, second.id])

        row = next(r for r in self.get_table_rows() if "Test Multi" in str(r))
        cells = row.find_all("td")
        address_cell = next(cell for cell in cells if "Zebra house A" in str(cell))
        postcode_cell = next(cell for cell in cells if "ZZ8 8ZZ" in str(cell))

        self.assertIn("Zebra house B", str(address_cell))
        self.assertEqual(len(address_cell.find_all("br")), 1)
        self.assertIn("ZZ9 9ZZ", str(postcode_cell))
        self.assertEqual(len(postcode_cell.find_all("br")), 1)

    def test_filter_has_search_and_show_hidden_records_checkbox(self):
        response = self.get_page()

        self.assertContains(response, "Search the data in the table")
        self.assertContains(response, "Hidden records")
        self.assertContains(response, "Show hidden records")
        self.assertNotContains(response, "Reassignment Status")
