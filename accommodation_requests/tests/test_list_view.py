from django.urls import reverse
from django.utils import timezone

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accommodation_requests.views import AccommodationRequestsTable
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import MvAccommodationRequestFactory as AccReqFactory
from user_management.tests.base import get_admin_user


class AccommodationRequestListViewTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def setUp(self):
        super().setUp()

        self.multi_la_ar = AccReqFactory(
            title="Test Multi LA",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            latest_application_date=timezone.now(),
            person_id=["1", "2", "3"],
            number_of_people=3,
            ltla_name=["Bridgend", "Kent"],
            utla_name=["Bridgend", "Kent"],
        )

        self.none_ltla = AccReqFactory(
            title="Test Multi LA",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            latest_application_date=timezone.now(),
            person_id=["1", "2", "3"],
            number_of_people=3,
            ltla_name=None,
            utla_name=[None],
        )

        self.empty_ar = AccReqFactory(
            title="Test Empty AR",
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_EMPTY,
            latest_application_date=timezone.now(),
            number_of_people=0,
            person_id=[],
            ltla_name=["test_ltla"],
            utla_name=["test_utla"],
        )

    def test_renders_multi_la(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:accommodation-requests",
            )
        )

        self.assertContains(response, "Accommodation requests")

        self.assertContains(response, "Name")
        self.assertContains(response, self.multi_la_ar.title)

        self.assertContains(response, "Status")
        self.assertContains(response, self.multi_la_ar.checks_status)

        self.assertContains(response, "Date of application")
        self.assertContains(
            response, self.multi_la_ar.latest_application_date.strftime("%-d %b %Y")
        )

        self.assertContains(response, "Number of people")
        self.assertContains(response, self.multi_la_ar.number_of_people)

        self.assertContains(response, "Lower tier LA")
        self.assertContains(
            response,
            AccommodationRequestsTable.format_array_as_string(
                None, self.multi_la_ar.get_all_ltla_names()
            ),
        )

        self.assertContains(response, "Upper tier LA")
        self.assertContains(
            response,
            AccommodationRequestsTable.format_array_as_string(
                None, self.multi_la_ar.get_all_utla_names()
            ),
        )

    def test_renders_with_none_ltla(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:accommodation-requests",
            )
        )

        self.assertContains(response, "Accommodation requests")

        self.assertContains(response, "Name")
        self.assertContains(response, self.multi_la_ar.title)

        self.assertContains(response, "Status")
        self.assertContains(response, self.multi_la_ar.checks_status)

        self.assertContains(response, "Date of application")
        self.assertContains(
            response, self.multi_la_ar.latest_application_date.strftime("%-d %b %Y")
        )

        self.assertContains(response, "Number of people")
        self.assertContains(response, self.multi_la_ar.number_of_people)

        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "-")

        self.assertContains(response, "Upper tier LA")
        self.assertContains(
            response,
            AccommodationRequestsTable.format_array_as_string(
                None, self.multi_la_ar.get_all_utla_names()
            ),
        )

    def test_does_not_render_empty_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:accommodation-requests",
            )
        )

        self.assertContains(response, "Accommodation requests")

        self.assertNotContains(response, self.empty_ar.title)
