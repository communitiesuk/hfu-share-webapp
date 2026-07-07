from datetime import datetime

from django.urls import reverse
from django.utils import timezone

from accommodation_requests.tests.base import AccommodationRequestsBaseTestCase
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import UserFactory
from ontology.models import CheckType, DevCheckV2, MvAccommodationRequest
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvGroupFactory,
    MvPersonFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_admin_user, get_la_user, get_mhclg_user
from webapp.mixins import SummaryListTestCaseMixin


class TestAccommodationRequestsSafeguardChecksTab(
    TestSessionTokenMixin, AccommodationRequestsBaseTestCase, SummaryListTestCaseMixin
):
    def test_shows_accommodation_and_sponsor_check(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        safeguarding_check_accommodation = (
            self.accommodation_suitable_check.accommodation.first()
        )

        self.assertContains(response, "Accommodation suitable")
        self.assertContains(
            response,
            safeguarding_check_accommodation.full_address,
        )

    def test_mhclg_user_can_view_update_checks(self):
        self.client.force_login(get_mhclg_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertContains(response, "View and update safeguarding checks")

    def test_does_not_show_accomm_suitable_check_not_directly_related_to_ar(self):
        accommodation = MvAccommodationFactory(
            full_address="new accommodation, city abc",
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
            is_principal=True,
        )
        accommodation_request = MvAccommodationRequestFactory(
            accommodation_id=[accommodation],
            primary_accommodation=accommodation,
        )
        accommodation_suitable_check_not_directly_related_to_ar = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
        )
        accommodation_suitable_check_not_directly_related_to_ar.accommodation.set(
            [accommodation]
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[accommodation_request.pk],
            )
        )

        self.assertContains(response, "Accommodation suitable")
        self.assertNotContains(
            response,
            accommodation.full_address,
        )

    def test_hides_accommodation_and_sponsor_check_recorded_outside_of_users_la(self):
        self.client.force_login(get_la_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        safeguarding_check_accommodation = (
            self.accommodation_suitable_check.accommodation.first()
        )

        self.assertContains(response, "Accommodation suitable")
        self.assertNotContains(
            response,
            safeguarding_check_accommodation.full_address,
        )

    def test_shows_accommodation_exists_check(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        safeguarding_check_accommodation = (
            self.accommodation_exists_check.accommodation.first()
        )

        self.assertContains(response, "Accommodation exists")
        self.assertContains(
            response,
            safeguarding_check_accommodation.full_address,
        )

    def test_shows_accommodation_exists_check_not_directly_related_to_ar(self):
        accommodation_request = MvAccommodationRequestFactory(
            primary_accommodation=self.accommodation_one,
            accommodation_id=[self.accommodation_one],
        )
        accommodation_exists_check_not_directly_related_to_ar = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
        )
        accommodation_exists_check_not_directly_related_to_ar.accommodation.set(
            [self.accommodation_one]
        )

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[accommodation_request.pk],
            )
        )

        self.assertContains(response, "Accommodation exists")
        self.assertContains(
            response,
            self.accommodation_one.full_address,
        )

    def test_hides_accommodation_exists_check_recorded_outside_of_users_la(self):
        self.client.force_login(get_la_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        safeguarding_check_accommodation = (
            self.accommodation_exists_check.accommodation.first()
        )

        self.assertContains(response, "Accommodation exists")
        self.assertNotContains(
            response,
            safeguarding_check_accommodation.full_address,
        )

    def test_shows_sponsor_dbs_check(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertContains(response, "DBS check and Sponsor suitable")
        self.assertContains(
            response,
            self.sponsor_1.get_full_name(),
        )
        # Duplicate record
        self.assertNotContains(
            response,
            self.dup_sponsor.get_full_name(),
        )

    def test_shows_sponsor_dbs_check_with_basic_dbs_type_tag(self):
        self.client.force_login(get_admin_user())

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = DevCheckV2.SponsorDBSPassedType.BASIC_DBS
        self.sponsor_dbs_check.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Basic",
        )

        # Duplicate record
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Basic",
        )

    def test_shows_sponsor_dbs_check_with_enhanced_dbs_type_tag(self):
        self.client.force_login(get_admin_user())

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = (
            DevCheckV2.SponsorDBSPassedType.ENHANCED_DBS
        )
        self.sponsor_dbs_check.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Enhanced",
        )

        # Duplicate record
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Enhanced",
        )

    def test_shows_sponsor_dbs_check_with_subtype_tag_if_legacy_formatted_subtype(self):
        self.client.force_login(get_admin_user())

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = "Enhanced"
        self.sponsor_dbs_check.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Enhanced",
        )

        # Duplicate record
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Enhanced",
        )

    def test_shows_sponsor_dbs_check_with_subtype_tag_if_unknown_subtype(self):
        self.client.force_login(get_admin_user())

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = "Unknown subtype"
        self.sponsor_dbs_check.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Unknown subtype",
        )

        # Duplicate record
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Unknown subtype",
        )

    def test_shows_sponsor_dbs_check_with_no_subtype_tag_if_none_subtype(self):
        self.client.force_login(get_admin_user())

        self.sponsor_dbs_check.check_status = DevCheckV2.CheckStatus.PASSED
        self.sponsor_dbs_check.check_subtype = None
        self.sponsor_dbs_check.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertSummaryListContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "Checks complete: Passed",
        )
        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.sponsor_1.get_full_name(),
            "None",
        )

        self.assertSummaryListNotContainsRowWithStatusTag(
            response,
            "DBS check and Sponsor suitable",
            self.dup_sponsor.get_full_name(),
            "Checks complete: Passed",
        )

    def test_hides_sponsor_dbs_check_recorded_outside_of_users_la(self):
        self.client.force_login(get_la_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertContains(response, "DBS check and Sponsor suitable")
        self.assertNotContains(
            response,
            self.sponsor_1.get_full_name(),
        )

    def test_shows_sponsor_dbs_check_related_to_active_host(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertContains(response, "DBS check and Sponsor suitable")
        self.assertContains(
            response,
            self.active_host.get_full_name(),
        )

        # Duplicate record
        self.assertNotContains(
            response,
            self.dup_sponsor.get_full_name(),
        )

    def test_shows_guest_has_arrived_check(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertContains(response, "Guests have arrived in their accommodation")

        # assert title shows up twice, once for each check
        self.assertContains(
            response, self.safeguarding_checks_accomodation_request.group.title, count=2
        )

    def test_shows_guest_has_arrived_check_for_merged_groups(self):
        main_group = MvGroupFactory(title="Test group")

        # child_group_1
        child_group_1 = MvGroupFactory(title="Child group 1", merged_group=main_group)

        # child_group_2
        MvGroupFactory(title="Child group 2", merged_group=main_group)

        ar = MvAccommodationRequestFactory(group=main_group)

        child_group_1_check_1 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
        )

        child_group_1_check_2 = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.GROUP_ARRIVED),
        )

        child_group_1.checks.set([child_group_1_check_1, child_group_1_check_2])
        ar.checks.set([child_group_1_check_1, child_group_1_check_2])

        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse("accommodation-requests:detail-safeguarding-checks", args=[ar.pk])
        )

        self.assertContains(response, "Guests have arrived in their accommodation")
        self.assertContains(response, child_group_1.title, count=2)

    def test_wont_show_audit_information_for_checks_no_user_or_date(self):
        self.client.force_login(get_admin_user())
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[self.safeguarding_checks_accomodation_request.pk],
            )
        )

        self.assertNotContains(response, "Created in previous system on Unknown time")

    def test_shows_audit_information(self):
        self.client.force_login(get_admin_user())
        user = UserFactory(id="999", username="testuser", email="test@example.com")

        accommodation = MvAccommodationFactory(
            full_address="accommodation one, city a",
            is_available_for_rematch=True,
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
        )
        sponsor = MvVolunteerFactory(first_name="Sponsor", last_name="1")
        guest = MvPersonFactory(first_name="John", last_name="Smith")

        ar = MvAccommodationRequestFactory(
            title="example AR",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            primary_accommodation=accommodation,
            accommodation_id=[accommodation],
            sponsor_id=[sponsor.pk],
            person_id=[guest.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        accommodation_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            check_status=DevCheckV2.CheckStatus.IN_PROGRESS,
            AR=[ar],
            last_updated_at=timezone.make_aware(datetime(2025, 1, 1, 12, 0, 0)),
            last_updated_by=user,
        )
        accommodation_suitable_check.accommodation.set([accommodation])

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[ar.pk],
            )
        )

        self.assertContains(response, "test@example.com on 1 January 2025 at 12:00pm")

    def test_audit_information_updates_when_check_updated(self):
        self.client.force_login(get_admin_user())
        user = UserFactory(id="999", username="testuser", email="test@example.com")

        user2 = UserFactory(id="1000", username="testuser2", email="test2@example.com")

        accommodation = MvAccommodationFactory(
            full_address="accommodation one, city a",
            is_available_for_rematch=True,
            ltla_name=self.ltla_name,
            utla_name=self.utla_name,
        )
        sponsor = MvVolunteerFactory(first_name="Sponsor", last_name="1")
        guest = MvPersonFactory(first_name="John", last_name="Smith")

        ar = MvAccommodationRequestFactory(
            title="example AR",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            primary_accommodation=accommodation,
            accommodation_id=[accommodation],
            sponsor_id=[sponsor.pk],
            person_id=[guest.pk],
            ltla_name=[self.ltla_name],
            utla_name=[self.utla_name],
        )

        accommodation_suitable_check = DevCheckV2Factory(
            check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            check_status=DevCheckV2.CheckStatus.IN_PROGRESS,
            AR=[ar],
            last_updated_at=timezone.make_aware(datetime(2025, 1, 1, 12, 0, 0)),
            last_updated_by=user,
        )
        accommodation_suitable_check.accommodation.set([accommodation])

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[ar.pk],
            )
        )

        self.assertContains(response, "test@example.com on 1 January 2025 at 12:00pm")

        # update check
        new_time = timezone.make_aware(datetime(2025, 1, 10, 14, 30, 0))
        accommodation_suitable_check.check_status = DevCheckV2.CheckStatus.PASSED
        accommodation_suitable_check.last_updated_at = new_time
        accommodation_suitable_check.last_updated_by = user2
        accommodation_suitable_check.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-safeguarding-checks",
                args=[ar.pk],
            )
        )

        self.assertNotContains(
            response, "test@example.com on 1 January 2025 at 12:00pm"
        )
        self.assertContains(response, "test2@example.com on 10 January 2025 at 2:30pm")
