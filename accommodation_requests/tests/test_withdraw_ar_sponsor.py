import http.client

from django.urls import reverse

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import (
    MvInteraction,
    MvVolunteer,
    SafeguardingNotification,
    SafeguardingReferral,
)
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_la_user,
    get_user_with_no_access,
)


class AccommodationRequestWithdrawSponsorTestCase(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase
):
    def test_should_return_409_for_ar_with_all_sponsors_withdrawn(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:withdraw-sponsor",
                args=[self.no_active_sponsors_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_409_for_ar_with_all_sponsors_within_user_la_withdrawn(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:withdraw-sponsor",
                args=[self.active_sponsor_from_other_la_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.CONFLICT)

    def test_should_return_404_for_ar_user_has_no_access_to(self):
        no_access_user = get_user_with_no_access()

        self.client.force_login(no_access_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:withdraw-sponsor",
                args=[self.all_active_sponsors_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_returns_withdraw_sponsor_form_for_ar_with_no_withdrawn_sponsors(self):
        user = get_admin_user()
        self.client.force_login(user)

        no_withdrawn_sponsor_accommodation_requests = [
            self.all_active_sponsors_req,
            self.null_withdrawn_sponsors_req,
        ]

        for accommodation_request in no_withdrawn_sponsor_accommodation_requests:
            response = self.client.get(
                reverse(
                    "accommodation-requests:withdraw-sponsor",
                    args=[accommodation_request.id],
                )
            )

            self.assertEqual(response.status_code, http.client.OK)
            self.assertContains(response, "Withdraw sponsor for")

            self.assertContains(response, "Select sponsors")
            self.assertContains(
                response,
                "Select the sponsors you want to withdraw.",
            )
            self.assertContains(response, "Reason for withdrawing sponsor")
            self.assertContains(
                response,
                "Add a reason for withdrawing the sponsor. "
                "Include the visa application number (GWF) "
                "for every visa that the sponsor is withdrawing from. "
                "The text you enter should be short and clear.",
            )

            self.assertContains(response, "Withdraw sponsor")
            self.assertContains(response, "Cancel")

    def test_returns_withdraw_sponsor_form_for_ar_with_some_withdrawn_sponsors(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:withdraw-sponsor",
                args=[self.partial_active_sponsor_req.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "Withdraw sponsor for")

        self.assertContains(response, "Select sponsors")
        self.assertContains(
            response,
            "Select the sponsors you want to withdraw.",
        )
        self.assertContains(response, "Reason for withdrawing sponsor")
        self.assertContains(
            response,
            "Add a reason for withdrawing the sponsor. "
            "Include the visa application number (GWF) "
            "for every visa that the sponsor is withdrawing from. "
            "The text you enter should be short and clear.",
        )

        self.assertContains(response, "Withdraw sponsor")
        self.assertContains(response, "Cancel")

    def test_withdraw_sponsor_form_lists_sponsors_if_multiple_active(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = self.all_active_sponsors_req
        response = self.client.get(
            reverse(
                "accommodation-requests:withdraw-sponsor",
                args=[accommodation_request.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

        for sponsor_id in accommodation_request.sponsor_id:
            sponsor = MvVolunteer.objects.get(id=sponsor_id)
            self.assertContains(response, sponsor.full_name)

    def test_withdraw_sponsor_form_does_not_list_sponsors_if_only_one_active(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = self.one_active_sponsor_req
        response = self.client.get(
            reverse(
                "accommodation-requests:withdraw-sponsor",
                args=[accommodation_request.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

        self.assertNotContains(response, "Select sponsors")
        self.assertNotContains(
            response,
            "Select the sponsors you want to withdraw.",
        )

        for sponsor_id in accommodation_request.sponsor_id:
            sponsor = MvVolunteer.objects.get(id=sponsor_id)
            self.assertNotContains(response, sponsor.full_name)

    def test_withdraw_sponsor_form_lists_only_active_sponsors_as_options(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = self.partial_active_sponsor_req
        response = self.client.get(
            reverse(
                "accommodation-requests:withdraw-sponsor",
                args=[accommodation_request.id],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

        for sponsor_id in accommodation_request.sponsor_id:
            sponsor = MvVolunteer.objects.get(id=sponsor_id)
            if sponsor_id in accommodation_request.sponsor_withdrawn:
                self.assertNotContains(response, sponsor.full_name)
            else:
                self.assertContains(response, sponsor.full_name)

    def test_withdraw_sponsor_updates_record_and_tracks_interaction(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = self.all_active_sponsors_req
        sponsors_to_be_withdrawn = accommodation_request.sponsor_id[:2]

        initial_interaction_count = MvInteraction.objects.count()

        response = self.client.post(
            f"/accommodation-requests/{accommodation_request.id}/withdraw-sponsor",
            {
                "sponsors": sponsors_to_be_withdrawn,
                "reason": "Test reason",
            },
        )

        self.assertEqual(response.status_code, http.client.FOUND)

        accommodation_request.refresh_from_db()
        self.assertEqual(
            accommodation_request.sponsor_withdrawn,
            [str(sponsor_id) for sponsor_id in sponsors_to_be_withdrawn],
        )
        self.assertEqual(accommodation_request.last_modified_by, user.get_full_name())
        self.assertEqual(MvInteraction.objects.count(), initial_interaction_count + 1)
        self.assertTrue(accommodation_request.edited_in_app)

        new_interaction = MvInteraction.objects.get(
            linked_accommodation_request=accommodation_request
        )
        self.assertEqual(
            new_interaction.interaction_contact,
            MvInteraction.InteractionContact.WITHDRAWN_SPONSOR,
        )
        self.assertEqual(
            new_interaction.interaction_type,
            MvInteraction.InteractionContact.WITHDRAWN_SPONSOR,
        )
        self.assertEqual(new_interaction.created_by, user)
        self.assertEqual(
            new_interaction.title,
            MvInteraction.InteractionContact.WITHDRAWN_SPONSOR,
        )

    def test_withdraw_sponsor_only_affects_target_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        sponsor = MvVolunteerFactory()
        ar1 = MvAccommodationRequestFactory(
            primary_sponsor_id=sponsor.id, sponsor_id=[sponsor.id]
        )
        ar2 = MvAccommodationRequestFactory(
            primary_sponsor_id=sponsor.id, sponsor_id=[sponsor.id]
        )
        guest1 = MvPersonFactory(accommodation_request=ar1)
        guest2 = MvPersonFactory(accommodation_request=ar2)
        ar1.person_id = [guest1.id]
        ar1.save()
        ar2.person_id = [guest2.id]
        ar2.save()

        # Withdraw sponsor from ar1 only
        response = self.client.post(
            reverse("accommodation-requests:withdraw-sponsor", args=[ar1.id]),
            {"sponsors": [sponsor.id], "reason": "Test reason"},
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success

        ar1_guest_ids = [guest1.id]
        ar2_guest_ids = [guest2.id]

        self.assertTrue(
            SafeguardingNotification.objects.filter(
                ar=ar1, sponsor_ids__contains=[sponsor.id]
            ).exists()
        )
        self.assertFalse(
            SafeguardingNotification.objects.filter(
                ar=ar2, sponsor_ids__contains=[sponsor.id]
            ).exists()
        )
        self.assertTrue(
            SafeguardingReferral.objects.filter(person_id__in=ar1_guest_ids).exists()
        )
        self.assertFalse(
            SafeguardingReferral.objects.filter(person_id__in=ar2_guest_ids).exists()
        )
