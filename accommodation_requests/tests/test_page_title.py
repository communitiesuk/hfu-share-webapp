from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvAccommodationRequest
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user


class AccommodationRequestPageTitlesTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.service_name = settings.SERVICE_NAME
        self.ar = MvAccommodationRequestFactory(
            primary_contact_first_name="Test",
            primary_contact_last_name="Title",
            title="Test Title",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
        )
        self.ar_no_surname = MvAccommodationRequestFactory(
            primary_contact_first_name="Test",
            title="Test Title",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
        )
        self.ar_no_primary = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED
        )
        self.closed_left_prog_acc_req = MvAccommodationRequestFactory(
            primary_contact_first_name="Test",
            primary_contact_last_name="Title",
            title="Test Title",
            checks_status=MvAccommodationRequest.ChecksStatus.CLOSED_LEFT_PROGRAMME,
        )
        self.sponsor_1 = MvVolunteerFactory(
            first_name="Sponsor", last_name="1", is_principal=True
        )
        self.all_active_sponsors_req = MvAccommodationRequestFactory(
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            primary_contact_first_name="Test",
            primary_contact_last_name="Title",
            title="Test Title",
            sponsor_id=[
                self.sponsor_1.pk,
            ],
            sponsor_withdrawn=[],
        )
        self.accommodation_one = MvAccommodationFactory(
            full_address="accommodation one, city a",
            is_available_for_rematch=True,
            ltla_name="test_ltla_name",
            utla_name="test_utla_name",
            is_principal=True,
        )
        self.guest = MvPersonFactory(first_name="John", last_name="Smith")
        self.one_guest_acc_req = MvAccommodationRequestFactory(
            primary_contact_first_name="Test",
            primary_contact_last_name="Title",
            title="Test Title",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            accommodation_id=[self.accommodation_one],
            number_of_people=1,
            person_id=[self.guest.pk],
            ltla_name=["test_ltla_name"],
            utla_name=["test_utla_name"],
        )

    def test_accommodation_request_detail_tab_titles(self):
        pages_and_titles = [
            (
                "accommodation-requests:detail-overview",
                f"Accommodation requests: TT, Overview - {self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:detail-safeguarding-checks",
                f"Accommodation requests: TT, Safeguarding checks - "
                f"{self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:update-safeguarding-checks",
                f"Accommodation requests: TT, Safeguarding checks - "
                f"{self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:detail-actions",
                f"Accommodation requests: TT, Actions - {self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:detail-linked-records",
                f"Accommodation requests: TT, Linked records - {self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:detail-properties",
                f"Accommodation requests: TT, Properties - {self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:detail-history",
                f"Accommodation requests: TT, History - {self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:close-for-guests",
                f"Accommodation requests: TT - {self.service_name}",
                self.ar.pk,
            ),
            (
                "accommodation-requests:reopen",
                f"Accommodation requests: TT - {self.service_name}",
                self.closed_left_prog_acc_req.pk,
            ),
            (
                "accommodation-requests:withdraw-sponsor",
                f"Accommodation requests: TT - {self.service_name}",
                self.all_active_sponsors_req.pk,
            ),
            (
                "accommodation-requests:rematch-guests",
                f"Accommodation requests: TT - {self.service_name}",
                self.one_guest_acc_req.pk,
            ),
            (
                "accommodation-requests:reassign-guests",
                f"Accommodation requests: TT - {self.service_name}",
                self.one_guest_acc_req.pk,
            ),
            (
                "accommodation-requests:move-guests",
                f"Accommodation requests: TT - {self.service_name}",
                self.one_guest_acc_req.pk,
            ),
            (
                "accommodation-requests:detail-comments",
                f"Accommodation requests: TT, Comments - {self.service_name}",
                self.ar.pk,
            ),
        ]

        user = get_admin_user()
        self.client.force_login(user)

        for view_name, expected_title, ar_pk in pages_and_titles:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(
                        view_name,
                        args=[ar_pk],
                    ),
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["TITLE"], expected_title)

    def test_guest_with_missing_surname(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[self.ar_no_surname.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            f"Accommodation requests: T, Overview - {self.service_name}",
        )

    def test_guest_with_missing_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-overview",
                args=[self.ar_no_primary.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["TITLE"],
            f"Accommodation requests: Overview - {self.service_name}",
        )
