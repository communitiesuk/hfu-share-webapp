from unittest.mock import call, patch

from django.urls import reverse
from django.utils import timezone

from accommodation_requests.forms import (
    AccommodationRequestUpdateSafeguardingChecksForm,
)
from accommodation_requests.tests.base import SafeguardingChecksBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import (
    CheckType,
    DevCheckV2,
    MvInteraction,
    SafeguardingNotification,
    SafeguardingReferral,
)
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user, get_la_user, get_mhclg_user


class AccommodationRequestUpdateSafeguardingChecksFormTests(
    SafeguardingChecksBaseTestCase
):
    def setUp(self):
        super().setUp()
        self.check_acomm_exists = CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS)
        self.check_acomm_suitable = CheckType.objects.get(
            id=CheckType.Id.ACCOMM_SUITABLE
        )
        self.check_sponsor_dbs = CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS)

        self.accom_exists_failure_reason = (
            DevCheckV2.AccommExistsFailureReason.NOT_RESIDENTIAL
        )
        self.accom_suitable_failure_reason = DevCheckV2.SuitabilityFailure.OVERCROWDED
        self.sponsor_dbs_type = DevCheckV2.SponsorDBSPassedType.BASIC_DBS

    def test_valid_accomm_exists_failed_requires_failure_and_accommodation(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_exists.pk,
            "status": DevCheckV2.CheckStatus.FAILED,
            "accommodation_exists_failure": self.accom_exists_failure_reason,
            "accommodations": self.accommodation.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.should_raise_escalation)

    def test_check_creation_creates_ltla_code(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_exists.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
            "accommodations": self.accommodation.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertTrue(form.is_valid())

        data = form.cleaned_data
        sg_check = form._create_or_update_sg_check(data)
        ltla_code = sg_check.ltla_code.all()
        self.assertEqual(1, ltla_code.count())
        self.assertEqual(ltla_code[0], self.uklocalauthority)

    def test_check_creation_missing_ltla_code_on_ar_doesnt_create_ltla_code(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_exists.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
            "accommodations": self.accommodation.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar2, user=user
        )
        self.assertTrue(form.is_valid())

        data = form.cleaned_data
        sg_check = form._create_or_update_sg_check(data)
        ltla_code = sg_check.ltla_code.all()
        self.assertEqual(0, ltla_code.count())

    def test_accomm_exists_failed_missing_failure_reason(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_exists.pk,
            "status": DevCheckV2.CheckStatus.FAILED,
            "accommodations": self.accommodation.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("accommodation_exists_failure", form.errors)

    def test_accomm_exists_missing_accommodation(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_exists.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("accommodations", form.errors)

    def test_accomm_suitable_failed_requires_failure_and_accommodation(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_suitable.pk,
            "status": DevCheckV2.CheckStatus.FAILED,
            "accommodation_suitable_failure": self.accom_suitable_failure_reason,
            "accommodations": self.accommodation.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )

        self.assertTrue(form.is_valid())
        self.assertTrue(form.should_raise_escalation)

    def test_accomm_suitable_failed_missing_failure_reason(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_suitable.pk,
            "status": DevCheckV2.CheckStatus.FAILED,
            "accommodations": self.accommodation.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("accommodation_suitable_failure", form.errors)

    def test_accomm_suitable_missing_accommodation(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_acomm_suitable.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("accommodations", form.errors)

    def test_sponsor_dbs_passed_requires_passed_type_and_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_sponsor_dbs.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
            "sponsor_dbs_passed": self.sponsor_dbs_type,
            "sponsors": self.sponsor.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertTrue(form.is_valid())
        self.assertFalse(form.should_raise_escalation)

    def test_sponsor_dbs_passed_missing_passed_type(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_sponsor_dbs.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
            "sponsors": self.sponsor.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("sponsor_dbs_passed", form.errors)

    def test_sponsor_dbs_missing_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        form_data = {
            "check_type": self.check_sponsor_dbs.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
            "sponsor_dbs_passed": self.sponsor_dbs_type,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data, instance=self.ar, user=user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("sponsors", form.errors)

    def test_should_raise_escalation_only_if_failed(self):
        user = get_admin_user()
        self.client.force_login(user)

        # status PASSED should not raise escalation for these types
        for check_type in [
            self.check_acomm_exists,
            self.check_acomm_suitable,
            self.check_sponsor_dbs,
        ]:
            form_data = {
                "check_type": check_type.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
            }
            form = AccommodationRequestUpdateSafeguardingChecksForm(
                data=form_data, instance=self.ar, user=user
            )
            form.is_valid()
            self.assertFalse(form.should_raise_escalation)

    def test_can_record_check_against_any_active_accommodations_on_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={}, instance=self.ar, user=user
        )

        accommodations = list(form.fields["accommodations"].queryset)

        self.assertEqual(accommodations, list(self.ar.get_accommodations()))

    def test_cannot_record_check_against_accommodations_outside_of_user_la(self):
        user = get_la_user()
        self.client.force_login(user)

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={}, instance=self.ar, user=user
        )

        fields = form.fields
        accommodations = list(fields["accommodations"].queryset)

        self.assertEqual(accommodations, [])

    def test_can_record_check_against_any_active_sponsors_on_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={}, instance=self.ar, user=user
        )

        sponsors = list(form.fields["sponsors"].queryset)

        self.assertEqual(sponsors, list(self.ar.get_active_sponsors()))

    def test_cannot_record_check_against_sponsors_outside_of_users_la(self):
        user = get_la_user()
        self.client.force_login(user)

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={}, instance=self.ar, user=user
        )

        fields = form.fields
        sponsors = list(fields["sponsors"].queryset)

        self.assertEqual(sponsors, [])

    def test_can_record_check_against_active_host_on_ar(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.ar.active_host = self.active_host
        self.ar.save()

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={}, instance=self.ar, user=user
        )

        sponsors = list(form.fields["sponsors"].queryset)

        self.assertEqual(
            sponsors, list(self.ar.get_active_sponsors()) + [self.active_host]
        )

    def test_status_field_excludes_unavailable(self):
        user = get_la_user()
        self.client.force_login(user)
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={}, instance=self.ar, user=user
        )
        status_choices = [c[0] for c in form.fields["status"].choices]
        self.assertNotIn(DevCheckV2.CheckStatus.UNAVAILABLE, status_choices)


class AccommodationRequestUserGroupSafeguardingChecksIntegrationTests(
    TestSessionTokenMixin, SafeguardingChecksBaseTestCase
):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "accommodation-requests:update-safeguarding-checks",
            kwargs={"pk": self.ar.pk},
        )

        self.check_sponsor_dbs = CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS)
        self.sponsor_dbs_type = DevCheckV2.SponsorDBSPassedType.BASIC_DBS
        self.check_acomm_exists = CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS)
        self.check_acomm_suitable = CheckType.objects.get(
            id=CheckType.Id.ACCOMM_SUITABLE
        )
        self.check_group_arrived = CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED)

        self.accom_exists_failure_reason = (
            DevCheckV2.AccommExistsFailureReason.NOT_RESIDENTIAL
        )

    def test_mhclg_user_can_update_sg_check(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "sponsors": self.sponsor.pk,
                "sponsor_dbs_failure": DevCheckV2.SponsorDBSFailureReason.NO_RESPONSE,
                "submit_and_leave": "1",
            },
        )
        self.assertEqual(response.status_code, 302)

        checks = DevCheckV2.objects.all()
        self.assertEqual(checks.count(), 1)
        check = checks.first()
        self.assertEqual(check.check_type, self.check_sponsor_dbs)
        self.assertEqual(check.check_status, DevCheckV2.CheckStatus.FAILED)


class AccommodationRequestUpdateSafeguardingChecksIntegrationTests(
    TestSessionTokenMixin, SafeguardingChecksBaseTestCase
):
    def setUp(self):
        super().setUp()
        self.user = get_admin_user()
        self.client.force_login(self.user)
        self.url = reverse(
            "accommodation-requests:update-safeguarding-checks",
            kwargs={"pk": self.ar.pk},
        )

        self.check_sponsor_dbs = CheckType.objects.get(id=CheckType.Id.SPONSOR_DBS)
        self.sponsor_dbs_type = DevCheckV2.SponsorDBSPassedType.BASIC_DBS
        self.check_acomm_exists = CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS)
        self.check_acomm_suitable = CheckType.objects.get(
            id=CheckType.Id.ACCOMM_SUITABLE
        )
        self.check_group_arrived = CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED)

        self.accom_exists_failure_reason = (
            DevCheckV2.AccommExistsFailureReason.NOT_RESIDENTIAL
        )

    def test_safeguarding_create_update_form_shows_side_table(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Safeguarding check completion check")

    def test_redirect_submit_and_stay(self):
        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "sponsor_dbs_passed": self.sponsor_dbs_type,
                "sponsors": self.sponsor.pk,
                "submit_and_stay": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)

    def test_redirect_submit_and_leave(self):
        detail_url = reverse(
            "accommodation-requests:detail-safeguarding-checks",
            kwargs={"pk": self.ar.pk},
        )
        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "sponsor_dbs_passed": self.sponsor_dbs_type,
                "sponsors": self.sponsor.pk,
                "submit_and_leave": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, detail_url)

    def test_form_validation_error_rendering(self):
        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sponsor is required for this check type.")
        self.assertContains(
            response, "Sponsor DBS passed type is required when status is passed."
        )

    def test_form_validation_error_rendering_for_ar_missing_group(self):
        accommodation_request = MvAccommodationRequestFactory(
            accommodation_id=[self.accommodation.pk],
            primary_sponsor=self.sponsor,
            group=None,
            person_id=[self.guest.id],
        )

        response = self.client.post(
            reverse(
                "accommodation-requests:update-safeguarding-checks",
                kwargs={"pk": accommodation_request.pk},
            ),
            data={
                "check_type": self.check_group_arrived.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We are unable to find the group for this check.")
        self.assertContains(
            response, "Please check the accommodation request is attached to a group."
        )

    def test_check_creation_and_referrals_for_sponsor_dbs_failed(self):
        initial_notification_count = SafeguardingNotification.objects.count()
        initial_referral_count = SafeguardingReferral.objects.count()

        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "sponsors": self.sponsor.pk,
                "sponsor_dbs_failure": DevCheckV2.SponsorDBSFailureReason.NO_RESPONSE,
                "submit_and_leave": "1",
            },
        )
        self.assertEqual(response.status_code, 302)

        checks = DevCheckV2.objects.all()
        self.assertEqual(checks.count(), 1)
        check = checks.first()
        self.assertEqual(check.check_type, self.check_sponsor_dbs)
        self.assertEqual(check.check_status, DevCheckV2.CheckStatus.FAILED)
        self.assertIn(self.sponsor, check.sponsor.all())

        # should create notifications for 2 AR, referrals for both AR and AR2 guests
        self.assertEqual(
            SafeguardingNotification.objects.count(), initial_notification_count + 2
        )
        self.assertEqual(
            SafeguardingReferral.objects.count(), initial_referral_count + 2
        )
        for notification in SafeguardingNotification.objects.all():
            self.assertEqual(notification.dev_check_v2.id, check.id)
        guests = [self.guest.pk, self.guest2.pk]
        for referral in SafeguardingReferral.objects.all():
            self.assertIn(referral.person.pk, guests)

    def test_check_creation_and_referrals_for_accommodation_exists_failed(self):
        initial_notification_count = SafeguardingNotification.objects.count()
        initial_referral_count = SafeguardingReferral.objects.count()

        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "accommodation_exists_failure": self.accom_exists_failure_reason,
                "accommodations": self.accommodation.pk,
                "submit_and_leave": "1",
            },
        )
        self.assertEqual(response.status_code, 302)

        checks = DevCheckV2.objects.all()
        self.assertEqual(checks.count(), 1)
        check = checks.first()
        self.assertEqual(check.check_type, self.check_acomm_exists)
        self.assertEqual(check.check_status, DevCheckV2.CheckStatus.FAILED)
        self.assertIn(self.accommodation, check.accommodation.all())

        # should create notifications for 2 AR, referrals for both AR and AR2 guests
        self.assertEqual(
            SafeguardingNotification.objects.count(), initial_notification_count + 2
        )
        self.assertEqual(
            SafeguardingReferral.objects.count(), initial_referral_count + 2
        )
        for notification in SafeguardingNotification.objects.all():
            self.assertEqual(notification.dev_check_v2.id, check.id)
        guests = [self.guest.pk, self.guest2.pk]
        for referral in SafeguardingReferral.objects.all():
            self.assertIn(referral.person.pk, guests)

    def test_populate_initial_from_existing_check(self):
        dcv2 = DevCheckV2.objects.create(
            id="test-dcv2-id",
            check_type=self.check_acomm_exists,
            check_status=DevCheckV2.CheckStatus.PASSED,
        )

        dcv2.AR.set([self.ar])
        dcv2.accommodation.set([self.accommodation])
        dcv2.save()

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={},
            instance=self.ar,
            dev_check_v2_id=dcv2.id,
            user=get_admin_user(),
        )
        form.populate_initial()

        self.assertEqual(form.initial["check_type"], dcv2.check_type)
        self.assertEqual(form.initial["status"], dcv2.check_status)
        self.assertEqual(form.initial["accommodations"], self.accommodation)

    def test_populate_initial_from_existing_check_handles_legacy_data_formatting(self):
        dcv2 = DevCheckV2.objects.create(
            id="test-dcv2-id",
            check_type=self.check_sponsor_dbs,
            check_status=DevCheckV2.CheckStatus.PASSED,
            check_subtype="Enhanced",
        )

        dcv2.sponsor.set([self.sponsor])
        dcv2.save()

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data={},
            instance=self.ar,
            dev_check_v2_id=dcv2.id,
            user=get_admin_user(),
        )
        form.populate_initial()

        self.assertEqual(form.initial["check_type"], dcv2.check_type)
        self.assertEqual(form.initial["status"], dcv2.check_status)
        self.assertEqual(
            form.initial["sponsor_dbs_passed"],
            DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS,
        )
        self.assertEqual(form.initial["sponsors"], self.sponsor)

    def test_incomplete_form_raises_error_when_missing_accommodation(self):
        form_data = {
            "check_type": self.check_acomm_exists.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
            "accommodations": None,
        }

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data,
            instance=self.ar,
            user=get_admin_user(),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "Accommodation is required for this check type.",
            form.errors["__all__"],
        )

    def test_incomplete_form_raises_error_when_missing_sponsor(self):
        form_data = {
            "check_type": self.check_sponsor_dbs,
            "status": DevCheckV2.CheckStatus.PASSED,
            "sponsors": None,
        }

        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data,
            instance=self.ar,
            user=get_admin_user(),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "Sponsor is required for this check type.",
            form.errors["__all__"],
        )

    def test_duplicate_check_raises_error_when_not_editing(self):
        dcv2 = DevCheckV2.objects.create(
            id="dupe-dcv2-id",
            check_type=self.check_acomm_exists,
            check_status=DevCheckV2.CheckStatus.PASSED,
        )

        dcv2.AR.set([self.ar])
        dcv2.accommodation.set([self.accommodation])
        dcv2.save()

        form_data = {
            "check_type": self.check_acomm_exists.pk,
            "status": DevCheckV2.CheckStatus.PASSED,
            "accommodations": self.accommodation.pk,
        }
        form = AccommodationRequestUpdateSafeguardingChecksForm(
            data=form_data,
            instance=self.ar,
            user=get_admin_user(),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "This check already exists. Please edit the existing check instead.",
            form.errors["__all__"],
        )

    def test_multiple_check_failures_do_not_create_duplicates(self):
        initial_notification_count = SafeguardingNotification.objects.count()
        initial_referral_count = SafeguardingReferral.objects.count()

        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "sponsors": self.sponsor.pk,
                "sponsor_dbs_failure": DevCheckV2.SponsorDBSFailureReason.NO_RESPONSE,
                "submit_and_leave": "1",
            },
        )
        self.assertEqual(response.status_code, 302)

        checks = DevCheckV2.objects.all()
        self.assertEqual(checks.count(), 1)
        check = checks.first()

        # should create notifications for 2 AR, referrals for both AR and AR2 guests
        self.assertEqual(
            SafeguardingNotification.objects.count(), initial_notification_count + 2
        )
        self.assertEqual(
            SafeguardingReferral.objects.count(), initial_referral_count + 2
        )
        for notification in SafeguardingNotification.objects.all():
            self.assertEqual(notification.dev_check_v2.id, check.id)
        guests = [self.guest.pk, self.guest2.pk]

        for referral in SafeguardingReferral.objects.all():
            self.assertIn(referral.person.pk, guests)

        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "accommodation_exists_failure": self.accom_exists_failure_reason,
                "accommodations": self.accommodation.pk,
                "submit_and_leave": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        checks = DevCheckV2.objects.all()
        self.assertEqual(checks.count(), 2)
        check = checks.first()

        # should not create new referrals
        self.assertEqual(
            SafeguardingReferral.objects.count(), initial_referral_count + 2
        )

    def test_guests_with_ar_in_accomm_are_linked_to_the_accomm_exists_failed_check(
        self,
    ):
        response = self.client.post(
            self.url,
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "accommodation_exists_failure": self.accom_exists_failure_reason,
                "accommodations": self.accommodation.pk,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        checks = DevCheckV2.objects.all()
        self.assertEqual(checks.count(), 1)
        check = checks.first()

        self.assertEqual(
            sorted([person.pk for person in check.person.all()]),
            sorted([self.guest.pk, self.guest2.pk]),
        )

    def test_created_interaction_when_accom_suitable_check_created(self):
        accommodation = MvAccommodationFactory()
        self.ar.primary_accommodation = accommodation
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_acomm_suitable.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "accommodations": accommodation.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Accommodation is suitable check: passed on "
            f"{timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )

    def test_created_interaction_when_existing_accom_suitable_check_edited(self):
        accommodation = MvAccommodationFactory()
        self.ar.primary_accommodation = accommodation
        self.ar.save()

        check = DevCheckV2.objects.create(
            id="test-check-id",
            check_type=self.check_acomm_suitable,
            check_status=DevCheckV2.CheckStatus.NOT_STARTED,
        )

        check.AR.set([self.ar])
        check.accommodation.set([accommodation])
        check.save()

        self.client.post(
            self.url,
            query_params={"dev_check_v2_id": check.id},
            data={
                "check_type": self.check_acomm_suitable.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "accommodations": accommodation.pk,
            },
            follow=True,
        )

        check.refresh_from_db()
        self.assertEqual(check.check_status, DevCheckV2.CheckStatus.PASSED)

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Accommodation is suitable check: passed on "
            f"{timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )

    def test_created_interaction_when_accom_exists_check_created(self):
        accommodation = MvAccommodationFactory()
        self.ar.primary_accommodation = accommodation
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "accommodations": accommodation.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Accommodation exists check: passed on "
            f"{timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
        )

    def test_created_interaction_when_existing_accom_exists_check_edited(self):
        accommodation = MvAccommodationFactory()
        self.ar.primary_accommodation = accommodation
        self.ar.save()

        check = DevCheckV2.objects.create(
            id="test-check-id",
            check_type=self.check_acomm_exists,
            check_status=DevCheckV2.CheckStatus.NOT_STARTED,
        )

        check.AR.set([self.ar])
        check.accommodation.set([accommodation])
        check.save()

        self.client.post(
            self.url,
            query_params={"dev_check_v2_id": check.id},
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "accommodations": accommodation.pk,
            },
            follow=True,
        )

        check.refresh_from_db()
        self.assertEqual(check.check_status, DevCheckV2.CheckStatus.PASSED)

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Accommodation exists check: passed on "
            f"{timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
        )

    def test_created_interaction_when_guests_arrived_check_created(self):
        group = MvGroupFactory()
        self.ar.group = group
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_group_arrived.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "group": group.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.GUEST_ARRIVED_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.GUEST_ARRIVED_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Guests have arrived in accommodation check: passed on "
            f"{timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.GUEST_ARRIVED_CHECK,
        )

    def test_created_interaction_when_existing_guests_arrived_check_edited(self):
        group = MvGroupFactory()
        self.ar.group = group
        self.ar.save()

        check = DevCheckV2.objects.create(
            id="test-check-id",
            check_type=self.check_group_arrived,
            check_status=DevCheckV2.CheckStatus.NOT_STARTED,
        )

        check.AR.set([self.ar])
        check.group.set([group])
        check.save()

        self.client.post(
            self.url,
            query_params={"dev_check_v2_id": check.id},
            data={
                "check_type": self.check_group_arrived.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "group": group.pk,
            },
            follow=True,
        )

        check.refresh_from_db()
        self.assertEqual(check.check_status, DevCheckV2.CheckStatus.PASSED)

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.GUEST_ARRIVED_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.GUEST_ARRIVED_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Guests have arrived in accommodation check: passed on "
            f"{timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.GUEST_ARRIVED_CHECK,
        )

    def test_creates_interaction_when_sponsor_check_created_and_in_progress(self):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        self.ar.primary_sponsor = sponsor
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.IN_PROGRESS,
                "sponsors": sponsor.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"DBS and sponsor suitable check: in progress on"
            f" {timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )

    def test_creates_interaction_when_existing_sponsor_check_edited(self):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        self.ar.primary_sponsor = sponsor
        self.ar.save()

        check = DevCheckV2.objects.create(
            id="test-check-id",
            check_type=self.check_group_arrived,
            check_status=DevCheckV2.CheckStatus.NOT_STARTED,
        )

        check.AR.set([self.ar])
        check.sponsor.set([sponsor])
        check.save()

        self.client.post(
            self.url,
            query_params={"dev_check_v2_id": check.id},
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.IN_PROGRESS,
                "sponsors": sponsor.pk,
            },
            follow=True,
        )

        check.refresh_from_db()
        self.assertEqual(check.check_status, DevCheckV2.CheckStatus.IN_PROGRESS)

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"DBS and sponsor suitable check: in progress on"
            f" {timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )

    def test_creates_interaction_when_basic_sponsor_check_created_and_passed(self):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        self.ar.primary_sponsor = sponsor
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "sponsor_dbs_passed": DevCheckV2.SponsorDBSPassedType.BASIC_DBS,
                "sponsors": sponsor.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Basic DBS check: passed on {timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            "DBS and sponsor suitable check: Basic DBS",
        )

    def test_creates_interaction_when_enhanced_sponsor_check_created_and_passed(self):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        self.ar.primary_sponsor = sponsor
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "sponsor_dbs_passed": DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS,
                "sponsors": sponsor.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Enhanced DBS check: passed on {timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            "DBS and sponsor suitable check: Enhanced DBS",
        )

    def test_creates_interaction_when_sponsor_check_created_and_failed_with_comment(
        self,
    ):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        self.ar.primary_sponsor = sponsor
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "sponsors": sponsor.pk,
                "sponsor_dbs_failure": DevCheckV2.SponsorDBSFailureReason.NO_RESPONSE,
                "notes": "Additional comments",
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Sponsor suitable check failed on "
            f"{timezone.now().strftime('%-d %B %Y')}. Reason: Sponsor has not responded"
            f" to communications.\nComments: Additional comments",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            "DBS and sponsor suitable check: failed",
        )

    def test_creates_interaction_when_sponsor_check_created_and_failed_without_comment(
        self,
    ):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        self.ar.primary_sponsor = sponsor
        self.ar.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "sponsors": sponsor.pk,
                "sponsor_dbs_failure": DevCheckV2.SponsorDBSFailureReason.NO_RESPONSE,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Sponsor suitable check failed on "
            f"{timezone.now().strftime('%-d %B %Y')}. Reason: "
            f"Sponsor has not responded to communications.",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            "DBS and sponsor suitable check: failed",
        )

    def test_creates_interaction_for_each_related_ar_when_sponsor_check_created(self):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        ar1 = MvAccommodationRequestFactory(
            primary_accommodation=self.accommodation,
            primary_sponsor=sponsor,
            group=self.group,
            person_id=[self.guest.id],
        )
        ar1.save()

        ar2 = MvAccommodationRequestFactory(
            accommodation_id=[self.accommodation.pk],
            primary_sponsor=self.sponsor,
            active_host=sponsor,
            group=self.group2,
            person_id=[self.guest2.id],
        )
        ar2.save()

        ar3 = MvAccommodationRequestFactory(
            accommodation_id=[self.accommodation.pk],
            primary_accommodation=self.accommodation2,
            primary_sponsor=self.sponsor2,
            sponsor_id=[sponsor.id, self.sponsor2.id],
            group=self.group3,
            person_id=[self.guest3.id],
        )
        ar3.save()

        self.client.post(
            reverse(
                "accommodation-requests:update-safeguarding-checks",
                kwargs={"pk": ar1.pk},
            ),
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "sponsor_dbs_passed": self.sponsor_dbs_type,
                "sponsors": sponsor.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 3)

        all_related_ars = [ar1, ar2, ar3]
        ars_with_interaction = []
        for interaction in MvInteraction.objects.all():
            linked_ar = interaction.linked_accommodation_request
            ars_with_interaction.append(linked_ar)

            self.assertEqual(
                interaction.interaction_contact,
                MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
            )
            self.assertEqual(
                interaction.interaction_type,
                MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
            )
            self.assertTrue(linked_ar in all_related_ars)
            self.assertEqual(
                interaction.interaction_notes,
                f"Basic DBS check: passed on {timezone.now().strftime('%-d %B %Y')}",
            )
            self.assertEqual(
                interaction.created_by, self.user if linked_ar == ar1 else None
            )
            self.assertEqual(
                interaction.title,
                "DBS and sponsor suitable check: Basic DBS",
            )

        self.assertEqual(set(ars_with_interaction), set(all_related_ars))

    def test_does_not_create_interaction_for_ar_when_sponsor_is_withdrawn(self):
        sponsor = MvVolunteerFactory(first_name="Unique", last_name="Sponsor")
        ar1 = MvAccommodationRequestFactory(
            primary_accommodation=self.accommodation,
            primary_sponsor=sponsor,
            group=self.group,
            person_id=[self.guest.id],
        )
        ar1.save()

        ar2 = MvAccommodationRequestFactory(
            accommodation_id=[self.accommodation.pk],
            primary_sponsor=self.sponsor,
            sponsor_id=[sponsor.id],
            sponsor_withdrawn=[sponsor.id],
            active_host=sponsor,
            group=self.group2,
            person_id=[self.guest2.id],
        )
        ar2.save()

        self.client.post(
            reverse(
                "accommodation-requests:update-safeguarding-checks",
                kwargs={"pk": ar1.pk},
            ),
            data={
                "check_type": self.check_sponsor_dbs.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "sponsor_dbs_passed": self.sponsor_dbs_type,
                "sponsors": sponsor.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.DBS_AND_SPONSOR_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, ar1)
        self.assertEqual(
            interaction.interaction_notes,
            f"Basic DBS check: passed on {timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            "DBS and sponsor suitable check: Basic DBS",
        )

    def test_creates_interaction_for_each_related_ar_when_accom_exists_check_created(
        self,
    ):
        accommodation = MvAccommodationFactory()
        ar1 = MvAccommodationRequestFactory(
            primary_accommodation=accommodation,
            primary_sponsor=self.sponsor,
            group=self.group,
            person_id=[self.guest.id],
        )
        ar1.save()

        ar2 = MvAccommodationRequestFactory(
            accommodation_id=[accommodation.pk],
            primary_sponsor=self.sponsor,
            group=self.group2,
            person_id=[self.guest2.id],
        )
        ar2.save()

        ar3 = MvAccommodationRequestFactory(
            accommodation_id=[accommodation.pk, self.accommodation2.pk],
            primary_accommodation=self.accommodation2,
            primary_sponsor=self.sponsor2,
            group=self.group3,
            person_id=[self.guest3.id],
        )
        ar3.save()

        self.client.post(
            reverse(
                "accommodation-requests:update-safeguarding-checks",
                kwargs={"pk": ar1.pk},
            ),
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "accommodation_exists_failure": self.accom_exists_failure_reason,
                "accommodations": accommodation.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 3)

        all_related_ars = [ar1, ar2, ar3]
        ars_with_interaction = []
        for interaction in MvInteraction.objects.all():
            linked_ar = interaction.linked_accommodation_request
            ars_with_interaction.append(linked_ar)

            self.assertEqual(
                interaction.interaction_contact,
                MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
            )
            self.assertEqual(
                interaction.interaction_type,
                MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
            )
            self.assertTrue(linked_ar in all_related_ars)
            self.assertEqual(
                interaction.interaction_notes,
                f"Accommodation exists check: failed on "
                f"{timezone.now().strftime('%-d %B %Y')}",
            )
            self.assertEqual(
                interaction.created_by, self.user if linked_ar == ar1 else None
            )
            self.assertEqual(
                interaction.title,
                MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
            )

        self.assertEqual(set(ars_with_interaction), set(all_related_ars))

    def test_does_not_create_interaction_for_ar_when_accommodation_is_only_previous(
        self,
    ):
        accommodation = MvAccommodationFactory()
        ar1 = MvAccommodationRequestFactory(
            primary_accommodation=accommodation,
            primary_sponsor=self.sponsor,
            group=self.group,
            person_id=[self.guest.id],
        )
        ar1.save()

        ar2 = MvAccommodationRequestFactory(
            accommodation_id=[self.accommodation2.pk],
            primary_sponsor=self.sponsor,
            group=self.group2,
            person_id=[self.guest2.id],
        )
        ar2.previous_accommodation.add(accommodation.id)
        ar2.save()

        # Edge case where guest has moved back into an accommodation they previously
        # moved out of
        ar3 = MvAccommodationRequestFactory(
            accommodation_id=[accommodation.pk],
            primary_accommodation=self.accommodation2,
            primary_sponsor=self.sponsor2,
            group=self.group3,
            person_id=[self.guest3.id],
        )
        ar3.previous_accommodation.add(accommodation.id)
        ar3.save()

        self.client.post(
            reverse(
                "accommodation-requests:update-safeguarding-checks",
                kwargs={"pk": ar1.pk},
            ),
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "accommodation_exists_failure": self.accom_exists_failure_reason,
                "accommodations": accommodation.pk,
            },
            follow=True,
        )

        # AR 2 has the accommodation as a previous accommodation ONLY, therefore it
        # should not have a related interaction
        all_related_ars = [ar1, ar3]
        ars_with_interaction = []
        for interaction in MvInteraction.objects.all():
            linked_ar = interaction.linked_accommodation_request
            ars_with_interaction.append(linked_ar)

            self.assertEqual(
                interaction.interaction_contact,
                MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
            )
            self.assertEqual(
                interaction.interaction_type,
                MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
            )
            self.assertTrue(linked_ar in all_related_ars)
            self.assertEqual(
                interaction.interaction_notes,
                f"Accommodation exists check: failed on "
                f"{timezone.now().strftime('%-d %B %Y')}",
            )
            self.assertEqual(
                interaction.created_by, self.user if linked_ar == ar1 else None
            )
            self.assertEqual(
                interaction.title,
                MvInteraction.InteractionContact.ACCOMMODATION_EXISTS_CHECK,
            )

        self.assertEqual(set(ars_with_interaction), set(all_related_ars))

    def test_creates_interaction_for_only_main_ar_when_accom_suitable_check_created(
        self,
    ):
        accommodation = MvAccommodationFactory()
        self.ar.primary_accommodation = accommodation
        self.ar.save()

        self.ar2.primary_accommodation = accommodation
        self.ar2.save()

        self.ar3.primary_accommodation = accommodation
        self.ar3.save()

        self.client.post(
            self.url,
            data={
                "check_type": self.check_acomm_suitable.pk,
                "status": DevCheckV2.CheckStatus.PASSED,
                "accommodations": accommodation.pk,
            },
            follow=True,
        )

        self.assertEqual(MvInteraction.objects.count(), 1)
        interaction = MvInteraction.objects.first()

        self.assertEqual(
            interaction.interaction_contact,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )
        self.assertEqual(
            interaction.interaction_type,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )
        self.assertEqual(interaction.linked_accommodation_request, self.ar)
        self.assertEqual(
            interaction.interaction_notes,
            f"Accommodation is suitable check: passed on "
            f"{timezone.now().strftime('%-d %B %Y')}",
        )
        self.assertEqual(interaction.created_by, self.user)
        self.assertEqual(
            interaction.title,
            MvInteraction.InteractionContact.ACCOMMODATION_SUITABLE_CHECK,
        )

    @patch("accommodation_requests.forms.sentry_sdk.metrics.count")
    def test_safeguarding_check_creates_sentry_metric(self, sentry_metrics):
        self.client.post(
            self.url,
            data={
                "check_type": self.check_acomm_exists.pk,
                "status": DevCheckV2.CheckStatus.FAILED,
                "accommodation_exists_failure": self.accom_exists_failure_reason,
                "accommodations": self.accommodation.pk,
            },
            follow=True,
        )

        expected_call_attributes = {
            "check_type": "Accommodation exists",
            "check_status": "Failed",
            "user_id": str(self.user.id),
        }

        self.assertEqual(sentry_metrics.call_count, 1)
        self.assertEqual(
            sentry_metrics.call_args_list,
            [call("safeguarding_check", 1, attributes=expected_call_attributes)],
        )
