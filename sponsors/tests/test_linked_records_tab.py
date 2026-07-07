from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import get_admin_user, get_da_user, get_la_user
from webapp.mixins import SummaryListTestCaseMixin


class SponsorsLinkedRecordsTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.uan = VisaApplicationFactory(
            ltla_name="ltla_somerset",
            application_unique_application_number="123456",
            title="Visa Application for Guest",
        )
        self.scottish_uan = VisaApplicationFactory(
            ltla_name="City of Edinburgh",
            application_unique_application_number="987654",
            title="Scottish Visa Application",
        )
        self.uan_other_la = VisaApplicationFactory(
            ltla_name="Other LTLA",
            utla_name="Other UTLA",
            application_unique_application_number="789101",
            title="Other LA Visa Application",
        )
        self.sponsor = MvVolunteerFactory(
            first_name="LA Sponsor",
            last_name="Spon",
            application_unique_application_number=[
                self.uan.application_unique_application_number,
                self.uan_other_la.application_unique_application_number,
            ],
        )

        self.scottish_sponsor = MvVolunteerFactory(
            first_name="Scottish Sponsor",
            last_name="Spon",
            application_unique_application_number=[
                self.scottish_uan.application_unique_application_number,
            ],
        )
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset",
            full_address="Somerset accommodation",
        )
        self.scottish_accommodation = MvAccommodationFactory(
            ltla_name="City of Edinburgh",
            full_address="Edinburgh accommodation",
        )
        self.scottish_accommodation.hosts.set([self.scottish_sponsor.id])
        self.accommodation.hosts.set([self.sponsor.id])
        self.accommodation_other_la = MvAccommodationFactory(
            ltla_name="Other LTLA",
            utla_name="Other UTLA",
            full_address="Other accommodation",
        )
        self.accommodation_other_la.hosts.set([self.sponsor.id])
        self.accommodation_on_ar_not_belonging_to_sponsor = MvAccommodationFactory(
            full_address="AR accommodation",
        )
        self.guest = MvPersonFactory(
            first_name="Guest",
            last_name="Person",
        )
        self.guest_other_la = MvPersonFactory(
            first_name="Other LA Guest",
            last_name="Person",
        )
        self.ar = MvAccommodationRequestFactory(
            title="Guest Person to Somerset accom",
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            primary_accommodation=self.accommodation,
            accommodation_id=[
                self.accommodation.id,
                self.accommodation_on_ar_not_belonging_to_sponsor.id,
            ],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.sponsor,
        )

        self.ar_other_la = MvAccommodationRequestFactory(
            title="Other LA Guest Person to Other accommod",
            ltla_name=["Other LA"],
            utla_name=["Other LA"],
            primary_accommodation=self.accommodation_other_la,
            accommodation_id=[self.accommodation_other_la.id],
            person_id=[self.guest_other_la.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.sponsor,
        )

        self.scottish_ar = MvAccommodationRequestFactory(
            title="Guest Person to Scottish accom",
            ltla_name=["City of Edinburgh"],
            primary_accommodation=self.scottish_accommodation,
            accommodation_id=[
                self.scottish_accommodation.id,
            ],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.scottish_sponsor,
            sponsor_id=[self.scottish_sponsor.id],
            active_host=self.scottish_sponsor,
        )
        self.active_host_ar = MvAccommodationRequestFactory(
            title="AR with sponsor as active host only",
            primary_sponsor=None,
            sponsor_id=[],
            active_host=self.sponsor,
        )
        self.primary_sponsor_ar = MvAccommodationRequestFactory(
            title="AR with sponsor as active host only",
            primary_sponsor=self.sponsor,
            sponsor_id=[],
            active_host=None,
        )
        self.sponsor_ar = MvAccommodationRequestFactory(
            title="AR with sponsor as active host only",
            primary_sponsor=None,
            sponsor_id=[self.sponsor.id],
            active_host=None,
        )

        self.guest.accommodation_request = self.ar
        self.guest.save()

        self.guest_other_la.accommodation_request = self.ar_other_la
        self.guest.save()

    def test_linked_records_should_display_related_ar_for_admin_user(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation requests", self.ar.title
        )
        self.assertSummaryListContainsRow(
            response, "Accommodation requests", self.ar_other_la.title
        )

    def test_linked_records_should_display_related_ar_for_da_user(
        self,
    ):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.scottish_sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")

    def test_should_display_only_related_accommodation_requests_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation requests", self.ar.title
        )
        self.assertSummaryListNotContainsRow(
            response, "Accommodation requests", self.ar_other_la.title
        )

    def test_should_display_withdrawn_tag_next_to_ar_if_sponsor_withdrawn(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.ar.sponsor_withdrawn = [self.sponsor.id]
        self.ar.active_host = None
        self.ar.save()

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRowWithStatusTag(
            response, "Accommodation requests", self.ar.title, "Withdrawn"
        )

    def test_should_not_display_withdrawn_tag_if_sponsor_withdrawn_but_also_active_host(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        self.ar.sponsor_withdrawn = [self.sponsor.id]
        self.ar.active_host = self.sponsor
        self.ar.save()

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation requests", self.ar.title
        )
        self.assertSummaryListNotContainsRowWithStatusTag(
            response, "Accommodation requests", self.ar.title, "Withdrawn"
        )

    def test_should_display_accommodation_requests_sponsor_is_only_active_host_on(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation requests", self.active_host_ar.title
        )

    def test_should_display_accommodation_requests_sponsor_is_only_primary_sponsor_on(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation requests", self.primary_sponsor_ar.title
        )

    def test_should_display_accommodation_requests_sponsor_is_only_sponsor_on(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation requests", self.sponsor_ar.title
        )

    def test_linked_records_should_display_related_accommodations(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation.full_address
        )
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation_other_la.full_address
        )

    def test_should_display_only_related_accommodations_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation.full_address
        )
        self.assertSummaryListNotContainsRow(
            response, "Accommodation", self.accommodation_other_la.full_address
        )

    def test_should_display_only_accommodations_directly_related_to_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation.full_address
        )
        self.assertSummaryListContainsRow(
            response, "Accommodation", self.accommodation_other_la.full_address
        )
        self.assertSummaryListNotContainsRow(
            response,
            "Accommodation",
            self.accommodation_on_ar_not_belonging_to_sponsor.full_address,
        )

    def test_linked_records_should_display_related_visa_applications(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertSummaryListContainsRow(response, "Visa applications", self.uan.title)
        self.assertSummaryListContainsRow(
            response, "Visa applications", self.uan_other_la.title
        )

    def test_should_display_only_related_visa_applications_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Visa applications")
        self.assertSummaryListContainsRow(response, "Visa applications", self.uan.title)
        self.assertSummaryListNotContainsRow(
            response, "Visa applications", self.uan_other_la.title
        )

    def test_linked_records_should_display_related_guests(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Guests")
        self.assertSummaryListContainsRow(response, "Guests", self.guest.first_name)
        self.assertSummaryListContainsRow(
            response, "Guests", self.guest_other_la.first_name
        )

    def test_should_display_only_related_guests_within_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "Linked records")
        self.assertContains(response, "Guests")
        self.assertSummaryListContainsRow(response, "Guests", self.guest.first_name)
        self.assertSummaryListNotContainsRow(
            response, "Guests", self.guest_other_la.first_name
        )

    def test_it_should_not_show_ars_if_excessive_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Mock the get_accommodation_requests_restrict_for_user method
        with patch.object(
            self.sponsor.__class__, "get_accommodation_requests_restrict_for_user"
        ) as mock_get_ars:
            # mock sponsor with over 1000 ARs attached
            mock_queryset = MagicMock()
            mock_queryset.count.return_value = 1001
            mock_queryset.exists.return_value = True
            mock_get_ars.return_value = mock_queryset

            response = self.client.get(
                reverse(
                    "sponsors:detail-linked-records",
                    args=[self.sponsor.pk],
                )
            )

            self.assertContains(response, "Linked records")
            self.assertSummaryListNotContainsRow(
                response, "Accommodation requests", self.sponsor_ar.title
            )
            self.assertSummaryListContainsRow(
                response,
                "Accommodation requests",
                "There are too many records to display.",
            )

    def test_it_wont_show_ar_excessive_sponsor_message_when_has_few_links(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Mock the get_accommodation_requests_restrict_for_user method
        with patch.object(
            self.sponsor.__class__, "get_accommodation_requests_restrict_for_user"
        ) as mock_get_ars:
            # mock sponsor with no ARs attached
            mock_queryset = MagicMock()
            mock_queryset.count.return_value = 0
            mock_queryset.exists.return_value = False
            mock_get_ars.return_value = mock_queryset

            response = self.client.get(
                reverse(
                    "sponsors:detail-linked-records",
                    args=[self.sponsor.pk],
                )
            )

            self.assertContains(response, "Linked records")
            self.assertSummaryListNotContainsRow(
                response,
                "Accommodation requests",
                "There are too many records to display.",
            )

    def test_it_wont_show_ar_exessive_sponsor_message_when_has_few_links(self):
        user = get_admin_user()
        self.client.force_login(user)

        # Mock the get_accommodation_requests_restrict_for_user method
        with patch.object(
            self.sponsor.__class__, "get_accommodation_requests_restrict_for_user"
        ) as mock_get_ars:
            # mock sponsor with one AR attached
            mock_queryset = MagicMock()
            mock_queryset.count.return_value = 1
            mock_queryset.exists.return_value = True
            mock_get_ars.return_value = mock_queryset

            response = self.client.get(
                reverse(
                    "sponsors:detail-linked-records",
                    args=[self.sponsor.pk],
                )
            )

            self.assertContains(response, "Linked records")
            self.assertSummaryListNotContainsRow(
                response,
                "Accommodation requests",
                "There are too many records to display.",
            )
