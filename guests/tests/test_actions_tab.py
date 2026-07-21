import http.client
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import GuestDuplicateGroupFactory
from ontology.models import ReassignmentRequest
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    ReassignmentRequestFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)
from webapp.mixins import SummaryListTestCaseMixin


class GuestsActionsTestCase(TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.guest = MvPersonFactory(
            first_name="LA Guest",
            last_name="Test",
        )

        self.first_guest = MvPersonFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            is_principal=False,
        )

        self.second_guest = MvPersonFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            is_principal=False,
        )

        self.third_guest = MvPersonFactory(
            first_name="test3firstname",
            last_name="test3lastname",
            is_principal=False,
        )

        self.further_duped_guest = MvPersonFactory(
            first_name="test1firstname",
            last_name="test2lastname",
            is_principal=False,
        )

        self.new_principal_guest = MvPersonFactory(
            first_name="test3firstname",
            last_name="test2lastname",
            is_principal=True,
        )

        guest_duplicate_group = GuestDuplicateGroupFactory.create(
            principal_record=self.further_duped_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        guest_duplicate_group.guests.set([self.first_guest, self.second_guest])
        guest_duplicate_group.save()

        guest_further_duplicate_group = GuestDuplicateGroupFactory.create(
            principal_record=self.new_principal_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        guest_further_duplicate_group.guests.set(
            [self.further_duped_guest, self.third_guest]
        )
        guest_further_duplicate_group.save()

        self.ltla_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=["person-2"],
            number_of_people=1,
        )
        self.ltla_guest = MvPersonFactory(
            pk="person-2",
            first_name="LTLA",
            last_name="Last",
            accommodation_request=self.ltla_accommodation_request,
        )

        self.da_accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["Aberdeenshire"],
            utla_name=["Aberdeenshire"],
            person_id=["person-3"],
            number_of_people=1,
        )
        self.da_guest = MvPersonFactory(
            pk="person-3",
            first_name="DA",
            last_name="Last",
            accommodation_request=self.da_accommodation_request,
        )

    def test_admin_user_is_allowed_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.guest.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)

    def test_ukvi_user_is_not_allowed_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.guest.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_mhclg_user_is_not_allowed_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.guest.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_service_support_user_is_not_allowed_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.guest.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_la_user_is_not_allowed_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.ltla_guest.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_da_user_is_not_allowed_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.da_guest.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.FORBIDDEN)

    def test_records_not_from_dedupes_show_no_actions(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.guest.pk],
            )
        )
        self.assertContains(response, "There are no actions available")

    def test_principal_records_created_from_dedupes_show_dupe_record_names(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.new_principal_guest.pk],
            )
        )

        self.assertContains(
            response,
            "Delete this record and restore separate records for",
        )

        self.assertContains(response, "test1firstname test2lastname")

        self.assertContains(response, "test3firstname test3lastname")

        self.assertContains(
            response,
            f'<a href="{
                reverse(
                    "deduplication:guests:undo-deduplication-records-manual-step",
                    kwargs={
                        "step": "view-duplicate-records",
                        "id": str(self.new_principal_guest.id),
                    },
                )
            }"',
        )

    def test_principal_records_used_in_further_dedup_show_cannot_be_undone(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "guests:detail-actions",
                args=[self.further_duped_guest.pk],
            )
        )

        self.assertContains(
            response,
            "This deduplication cannot yet be undone due to a further "
            "deduplication. To restore this record, first undo the deduplication "
            "from the",
        )

        self.assertRegex(
            response.content.decode(),
            r"<a href=/guests/\d+/actions>actions tab for "
            "test3firstname test2lastname.</a>",
        )

        self.assertContains(
            response, "A full deduplication history is in the history tab."
        )

        self.assertNotContains(response, "Start")


class GuestsActionsBlockedByReassignmentTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

        self.first_guest = MvPersonFactory(is_principal=True)
        self.second_guest = MvPersonFactory(is_principal=True)
        self.principal_guest = MvPersonFactory(is_principal=True)

        self.dup_group = GuestDuplicateGroupFactory.create(
            principal_record=self.principal_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.guests.set([self.first_guest, self.second_guest])
        self.dup_group.save()

    def _get_actions_response(self):
        user = get_admin_user()
        self.client.force_login(user)
        return self.client.get(
            reverse("guests:detail-actions", args=[self.principal_guest.pk])
        )

    def _undo_deduplication_url(self):
        return reverse(
            "deduplication:guests:undo-deduplication-records-manual-step",
            kwargs={
                "step": "view-duplicate-records",
                "id": str(self.principal_guest.id),
            },
        )

    def test_principal_records_with_pre_dedup_reassignment_show_undo_action(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            responded_at=datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        response = self._get_actions_response()

        self.assertContains(response, f'<a href="{self._undo_deduplication_url()}"')

    def test_principal_records_with_pending_reassignment_do_not_show_undo_action(self):
        rr = ReassignmentRequestFactory(outcome=ReassignmentRequest.Outcome.PENDING)
        rr.guests.set([self.principal_guest])

        response = self._get_actions_response()

        self.assertNotContains(response, f'<a href="{self._undo_deduplication_url()}"')

    def test_pending_reassignment_blocking_message_is_visible(self):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.PENDING,
            destination_ltla_name="Barking and Dagenham",
        )
        rr.guests.set([self.principal_guest])

        response = self._get_actions_response()

        self.assertContains(
            response,
            f"You sent a request to move this guest to {rr.destination_ltla_name}. "
            f"You cannot undo this deduplication while there is a "
            f'<a class="govuk-link" href='
            f'"{reverse("reassignment-requests:detail-received", kwargs={"pk": rr.id})}">'  # noqa: E501
            f"pending request to move this guest</a>.",
        )

    def test_principal_records_with_post_dedup_reassignment_do_not_show_undo_action(
        self,
    ):
        rr = ReassignmentRequestFactory(
            outcome=ReassignmentRequest.Outcome.ACCEPTED,
            responded_at=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        )
        rr.guests.set([self.principal_guest])

        response = self._get_actions_response()

        self.assertNotContains(response, f'<a href="{self._undo_deduplication_url()}"')


class GuestsActionsBlockedByMultiLaAccommodationRequestTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()

        self.first_guest = MvPersonFactory(is_principal=True)
        self.second_guest = MvPersonFactory(is_principal=True)

        self.ar = MvAccommodationRequestFactory(ltla_name=["Barking and Dagenham"])
        self.principal_guest = MvPersonFactory(
            is_principal=True,
            accommodation_request=self.ar,
        )

        self.dup_group = GuestDuplicateGroupFactory.create(
            principal_record=self.principal_guest,
            created_at=datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc),
        )
        self.dup_group.guests.set([self.first_guest, self.second_guest])
        self.dup_group.save()

    def _get_actions_response(self):
        user = get_admin_user()
        self.client.force_login(user)
        return self.client.get(
            reverse("guests:detail-actions", args=[self.principal_guest.pk])
        )

    def _undo_deduplication_url(self):
        return reverse(
            "deduplication:guests:undo-deduplication-records-manual-step",
            kwargs={
                "step": "view-duplicate-records",
                "id": str(self.principal_guest.id),
            },
        )

    def test_principal_records_with_single_la_ar_show_undo_action(
        self,
    ):
        response = self._get_actions_response()

        self.assertContains(response, f'<a href="{self._undo_deduplication_url()}"')

    def test_principal_records_with_multi_la_ar_do_not_show_undo_action(
        self,
    ):
        self.ar.ltla_name = ["Barking and Dagenham", "Camden"]
        self.ar.save()

        response = self._get_actions_response()

        self.assertNotContains(response, f'<a href="{self._undo_deduplication_url()}"')

    def test_multi_la_blocking_message_is_visible(self):
        self.ar.ltla_name = ["Barking and Dagenham", "Camden"]
        self.ar.save()

        response = self._get_actions_response()

        self.assertContains(
            response,
            "This guest is linked to multiple local authorities "
            "(LAs) so deduplication cannot be undone.",
        )
