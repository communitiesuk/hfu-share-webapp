from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    PersonMasterRecordFactory,
    SponsorMasterRecordFactory,
)
from user_management.tests.base import get_admin_user


class SponsorLinkedRecordsHistoricGuestDedupTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="Sponsor", last_name="Host", is_principal=True
        )
        self.duplicate_guest = MvPersonFactory(
            first_name="Old", last_name="Duplicate", is_principal=False
        )
        self.principal_guest = MvPersonFactory(
            first_name="New", last_name="Principal", is_principal=True
        )

        master_record = PersonMasterRecordFactory(principal_record=self.principal_guest)
        master_record.persons.add(self.duplicate_guest, self.principal_guest)

        self.ar = MvAccommodationRequestFactory(
            title="AR with historic deduplicated guest",
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.sponsor,
            person_id=[self.duplicate_guest.id],
            number_of_people=1,
        )
        self.duplicate_guest.accommodation_request = self.ar
        self.duplicate_guest.save()

    def test_sponsor_linked_records_shows_principal_guest_not_stale_duplicate(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("sponsors:detail-linked-records", args=[self.sponsor.pk])
        )

        self.assertContains(response, self.principal_guest.get_full_name())
        self.assertNotContains(response, self.duplicate_guest.get_full_name())


class SponsorLinkedRecordsGuestMissingMasterRecordTestCase(
    TestSessionTokenMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="Sponsor", last_name="Host", is_principal=True
        )
        self.orphaned_duplicate_guest = MvPersonFactory(
            first_name="Orphaned", last_name="Duplicate", is_principal=False
        )
        self.ar = MvAccommodationRequestFactory(
            title="AR with a duplicate guest missing its master record",
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.sponsor,
            person_id=[self.orphaned_duplicate_guest.id],
            number_of_people=1,
        )
        self.orphaned_duplicate_guest.accommodation_request = self.ar
        self.orphaned_duplicate_guest.save()

    def test_falls_back_to_showing_duplicate_when_no_master_record_exists(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse("sponsors:detail-linked-records", args=[self.sponsor.pk])
        )

        self.assertContains(
            response, self.orphaned_duplicate_guest.get_full_name()
        )


class SponsorLinkedRecordsHistoricSponsorDedupTestCase(TestSessionTokenMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.duplicate_sponsor = MvVolunteerFactory(
            first_name="Old", last_name="Sponsor", is_principal=False
        )
        self.principal_sponsor = MvVolunteerFactory(
            first_name="New", last_name="Sponsor", is_principal=True
        )
        master_record = SponsorMasterRecordFactory(
            principal_record=self.principal_sponsor
        )
        master_record.sponsors.add(self.duplicate_sponsor, self.principal_sponsor)

        self.ar = MvAccommodationRequestFactory(
            title="AR still linked to historic deduplicated sponsor",
            primary_sponsor=self.duplicate_sponsor,
            sponsor_id=[self.duplicate_sponsor.id],
            active_host=self.duplicate_sponsor,
            number_of_people=1,
        )

    def test_principal_sponsor_linked_records_shows_ar_still_pointing_at_duplicate(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-linked-records", args=[self.principal_sponsor.pk]
            )
        )

        self.assertContains(response, self.ar.title)
