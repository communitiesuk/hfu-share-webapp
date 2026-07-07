from datetime import datetime, timezone

from django.test import TestCase
from freezegun import freeze_time

from accounts.tests.factories import UserFactory
from ontology.admin_stats import (
    generate_monthly_audit_stats,
    get_report_end_date,
    get_user_stats,
)
from ontology.models import CheckType
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
    MvVolunteerFactory,
)


class MonthlyAuditStatsTest(TestCase):
    def test_generate_monthly_audit_stats(self):
        # Create some objects at various times, to show up in the monthly stats

        with freeze_time(datetime(2026, 1, 1, tzinfo=timezone.utc)):
            postcode = MvUkPostcodeFactory()
            MvAccommodationFactory(postcode=postcode)
            sponsor = MvVolunteerFactory(is_principal=True)
            person = MvPersonFactory(accommodation_request=None)

        with freeze_time(datetime(2026, 2, 1, tzinfo=timezone.utc)):
            MvAccommodationRequestFactory(
                primary_sponsor=sponsor, person_id=[person.id]
            )

            DevCheckV2Factory(
                check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_EXISTS),
            )

        # Partial stats from current month are included
        with freeze_time(datetime(2026, 3, 1, tzinfo=timezone.utc)):
            DevCheckV2Factory(
                check_type=CheckType.objects.get(id=CheckType.Id.ACCOMM_SUITABLE),
            )

        with freeze_time(datetime(2026, 3, 2, tzinfo=timezone.utc)):
            # Default start date of 1 Jan 2026
            stats = generate_monthly_audit_stats()

        assert stats == {
            "MvAccommodation": {
                "Total changes": 1,
                "January 2026": 1,
                "February 2026": 0,
                "March 2026": 0,
            },
            "MvAccommodationRequest": {
                "Total changes": 1,
                "January 2026": 0,
                "February 2026": 1,
                "March 2026": 0,
            },
            "DevCheckV2": {
                "Total changes": 2,
                "January 2026": 0,
                "February 2026": 1,
                "March 2026": 1,
            },
            "MvInteraction": {
                "Total changes": 0,
                "January 2026": 0,
                "February 2026": 0,
                "March 2026": 0,
            },
            "MvGroup": {
                "Total changes": 0,
                "January 2026": 0,
                "February 2026": 0,
                "March 2026": 0,
            },
            "MvPerson": {
                "Total changes": 1,
                "January 2026": 1,
                "February 2026": 0,
                "March 2026": 0,
            },
            "MvVolunteer": {
                "Total changes": 1,
                "January 2026": 1,
                "February 2026": 0,
                "March 2026": 0,
            },
            "ReassignmentRequest": {
                "Total changes": 0,
                "January 2026": 0,
                "February 2026": 0,
                "March 2026": 0,
            },
            "SafeguardingReferral": {
                "Total changes": 0,
                "January 2026": 0,
                "February 2026": 0,
                "March 2026": 0,
            },
            "VisaInformationRequest": {
                "Total changes": 0,
                "January 2026": 0,
                "February 2026": 0,
                "March 2026": 0,
            },
        }

    def test_get_report_end_date_returns_first_of_next_month(self):
        with freeze_time(datetime(2026, 1, 31, tzinfo=timezone.utc)):
            result = get_report_end_date()
        self.assertEqual(result, datetime(2026, 2, 1, tzinfo=timezone.utc))

    def test_generate_monthly_audit_stats_handles_new_year(self):
        with freeze_time(datetime(2026, 12, 17, tzinfo=timezone.utc)):
            MvVolunteerFactory(is_principal=True)
        with freeze_time(datetime(2027, 1, 2, tzinfo=timezone.utc)):
            MvVolunteerFactory(is_principal=True)

        with freeze_time(datetime(2027, 2, 6, tzinfo=timezone.utc)):
            stats = generate_monthly_audit_stats(
                start_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
            )

        assert stats["MvVolunteer"] == {
            "Total changes": 2,
            "December 2026": 1,
            "January 2027": 1,
            "February 2027": 0,
        }


class MonthlyUserStatsTest(TestCase):
    def test_get_user_stats_returns_correct_info(self):
        # User 1 joined 91 days ago
        user1 = UserFactory()
        user1_join_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
        user1.last_login = user1_join_date
        user1.date_joined = user1_join_date
        user1.save(update_fields=["last_login", "date_joined"])

        # User 2 joined 90 days ago and logged in
        user2 = UserFactory()
        user2_join_date = datetime(2026, 1, 2, tzinfo=timezone.utc)
        user2.last_login = user2_join_date
        user2.date_joined = user2_join_date
        user2.save(update_fields=["last_login", "date_joined"])

        # User 3 joined 90 days ago but hasn't logged in
        user3 = UserFactory()
        user3_join_date = datetime(2026, 1, 2, tzinfo=timezone.utc)
        user3.date_joined = user3_join_date
        user3.last_login = None
        user3.save(update_fields=["last_login", "date_joined"])

        # Call the function 91 days after User 1 last logged in
        with freeze_time(datetime(2026, 4, 2, tzinfo=timezone.utc)):
            user_stats = get_user_stats()

        assert user_stats == {
            "total_users": 3,
            "users_active_in_last_90_days": 1,
            "new_users_in_last_90_days": 2,
        }
