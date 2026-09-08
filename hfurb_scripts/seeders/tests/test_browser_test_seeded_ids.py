from django.db.models import Q
from django.test import override_settings

from accounts.enums import (
    BROWSER_TEST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    GroupType,
)
from accounts.tests.factories import GroupFactory, UserFactory
from deduplication.models import GuestDuplicateGroup, SponsorDuplicateGroup
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    APP_CREATED_RECORDS,
    SEEDED_ID_START,
    _linked_to_seeded_records,
    seed_browser_test_la,
)
from ontology.models import MvAccommodationRequest, ReassignmentRequest
from test_utils.base import BaseTestCase


@override_settings(ENVIRONMENT="dev")
class BrowserTestSeededIdsTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        group = GroupFactory(
            name=BROWSER_TEST_LA_GROUP_NAME,
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__utla_name="Hobbiton (Browser test UTLA)",
            groupinfo__da_name="England",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
        )
        UserFactory().groups.add(group)
        seed_browser_test_la()

    def test_records_created_through_application_code_get_browser_test_ids(self):
        for model, _id_kind, link_fields in APP_CREATED_RECORDS:
            with self.subTest(model.__name__):
                unprefixed = (
                    model._base_manager.filter(_linked_to_seeded_records(link_fields))
                    .exclude(pk__startswith=SEEDED_ID_START)
                    .distinct()
                )
                self.assertQuerySetEqual(unprefixed, [])

    def test_reassignment_requests_in_the_browser_test_la_get_browser_test_ids(self):
        ltla_name = BROWSER_TEST_LTLA_NAMES[0]
        unprefixed = ReassignmentRequest.objects.filter(
            Q(source_ltla_name__overlap=[ltla_name])
            | Q(destination_ltla_name=ltla_name)
        ).exclude(pk__startswith=SEEDED_ID_START)

        self.assertQuerySetEqual(unprefixed, [])

    def test_only_deduplication_principals_keep_application_ids(self):
        seeded_ars = MvAccommodationRequest._base_manager.filter(
            pk__startswith=SEEDED_ID_START
        )
        linked_person_ids = {pid for ar in seeded_ars for pid in ar.person_id or []}
        linked_sponsor_ids = {sid for ar in seeded_ars for sid in ar.sponsor_id or []}
        guest_group = GuestDuplicateGroup._base_manager.distinct().get(
            guests__id__startswith=SEEDED_ID_START
        )
        sponsor_group = SponsorDuplicateGroup._base_manager.distinct().get(
            sponsors__id__startswith=SEEDED_ID_START
        )

        unprefixed_people = {
            pid for pid in linked_person_ids if not pid.startswith(SEEDED_ID_START)
        }
        unprefixed_sponsors = {
            sid for sid in linked_sponsor_ids if not sid.startswith(SEEDED_ID_START)
        }

        self.assertEqual(unprefixed_people, {guest_group.principal_record_id})
        self.assertEqual(unprefixed_sponsors, {sponsor_group.principal_record_id})
