from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from deduplication.tests.factories import SponsorDuplicateGroupFactory
from ontology.models import MvVolunteer
from ontology.tests.factories import MvVolunteerFactory
from user_management.tests.base import get_admin_user


class SponsorDeduplicationHistoryViewTest(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.first_sponsor = MvVolunteerFactory(
            first_name="test1firstname",
            last_name="test1lastname",
            sex="Female",
            date_of_birth=datetime(1999, 11, 11, tzinfo=timezone.utc),
            age=26,
            email="test@example.com",
            phone_number=["01134960698"],
            residential_postcodes=["OX1 1OX"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )

        self.second_sponsor = MvVolunteerFactory(
            first_name="test2firstname",
            last_name="test2lastname",
            sex="Male",
            date_of_birth=datetime(1981, 6, 10, tzinfo=timezone.utc),
            email="test2@example.com",
            phone_number=["04467123455"],
            residential_postcodes=["NW1 1WN"],
            flag_unsuitable=False,
            is_principal=True,
            sponsor_type=MvVolunteer.SponsorType.INDIVIDUAL,
        )
        self.duplicate_group = SponsorDuplicateGroupFactory()
        self.duplicate_group.sponsors.add(self.first_sponsor, self.second_sponsor)
        self.duplicate_group.save()
        self.duplicate_group.deduplicate(
            principal_record_values={
                "first_name": self.first_sponsor.first_name,
                "last_name": self.second_sponsor.last_name,
                "sex": self.second_sponsor.sex,
                "date_of_birth": self.first_sponsor.date_of_birth,
                "age": self.first_sponsor.age,
                "email": self.second_sponsor.email,
                "phone_number": self.second_sponsor.phone_number,
                "residential_postcodes": self.first_sponsor.residential_postcodes,
                "flag_unsuitable": self.second_sponsor.flag_unsuitable,
                "is_principal": True,
                "sponsor_type": MvVolunteer.SponsorType.INDIVIDUAL,
            },
            user=get_admin_user(),
        )

    def test_history_view_shows_deduplication_event_on_first_sponsor(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.first_sponsor.pk],
            )
        )
        self.assertContains(response, "Record deduplicated")
        self.assertContains(
            response,
            f"This record, and sponsor and host record {self.second_sponsor.full_name}"
            f" were marked as duplicates. New principal record is"
            f" {self.duplicate_group.principal_record.full_name}.",
        )

    def test_history_view_shows_deduplication_event_on_second_sponsor(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.second_sponsor.pk],
            )
        )
        self.assertContains(response, "Record deduplicated")
        self.assertContains(
            response,
            f"This record, and sponsor and host record {self.first_sponsor.full_name}"
            f" were marked as duplicates. "
            f"New principal record is "
            f"{self.duplicate_group.principal_record.full_name}.",
        )

    def test_history_view_shows_deduplication_event_on_principal_sponsor(self):
        self.client.force_login(get_admin_user())

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.duplicate_group.principal_record.pk],
            )
        )
        self.assertContains(response, "Record deduplicated")
        self.assertContains(
            response,
            f"This record was created after sponsor and host records "
            f"{self.first_sponsor.full_name} and {self.second_sponsor.full_name} "
            f"were marked as duplicates.",
        )

    def test_history_view_shows_undeduplication_event_on_first_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.duplicate_group.undo_deduplication(user=user)
        url = reverse("sponsors:detail-history", kwargs={"pk": self.first_sponsor.pk})
        response = self.client.get(url)
        self.assertContains(response, "Deduplication undone")
        self.assertContains(
            response,
            f"This record, and sponsor and host record {self.second_sponsor.full_name}"
            f" were restored as separate principal records. A principal record"
            f" combining data from both was deleted.",
        )

    def test_history_view_shows_undeduplication_event_on_second_sponsor(self):
        user = get_admin_user()
        self.client.force_login(user)

        self.duplicate_group.undo_deduplication(user=user)
        url = reverse("sponsors:detail-history", kwargs={"pk": self.second_sponsor.pk})
        response = self.client.get(url)
        self.assertContains(response, "Deduplication undone")
        self.assertContains(
            response,
            f"This record, and sponsor and host record {self.first_sponsor.full_name}"
            f" were restored as separate principal records. A principal record"
            f" combining data from both was deleted.",
        )
