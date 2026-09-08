import json
import re

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
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
    DEDUPLICATION_PRINCIPALS,
    RECORDS_LINKED_TO_SEEDED_RECORDS,
    SEEDED_ID_START,
    _linked_to_seeded_records,
    seed_browser_test_la,
)
from ontology.models import (
    DevCheckV2,
    MvAccommodationRequest,
    MvInteraction,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingNotification,
)
from test_utils.base import BaseTestCase

SEEDED_MODELS = [
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    MvInteraction,
    DevCheckV2,
    SafeguardingNotification,
    ReassignmentRequest,
]


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
        renamed_records = DEDUPLICATION_PRINCIPALS + RECORDS_LINKED_TO_SEEDED_RECORDS
        for model, _id_kind, link_fields in renamed_records:
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

    def test_deduplication_principals_get_browser_test_ids(self):
        seeded_ars = MvAccommodationRequest._base_manager.filter(
            pk__startswith=SEEDED_ID_START
        )
        linked_ids = {
            linked_id
            for ar in seeded_ars
            for linked_id in (ar.person_id or []) + (ar.sponsor_id or [])
        }

        unprefixed = {i for i in linked_ids if not i.startswith(SEEDED_ID_START)}

        self.assertEqual(unprefixed, set())

    def test_no_application_minted_ids_remain_in_seeded_data(self):
        application_minted_id = re.compile(
            r"(person|sponsor|accommodation|interaction|rr)-[0-9a-f]{8}-"
        )
        seeded_text = json.dumps(
            serializers.serialize("python", _all_seeded_records()),
            cls=DjangoJSONEncoder,
        )

        self.assertIsNone(application_minted_id.search(seeded_text))


def _all_seeded_records() -> list:
    records: list = []
    for model in SEEDED_MODELS:
        records.extend(model._base_manager.filter(pk__startswith=SEEDED_ID_START))
    records.extend(
        GuestDuplicateGroup._base_manager.filter(
            guests__id__startswith=SEEDED_ID_START
        ).distinct()
    )
    records.extend(
        SponsorDuplicateGroup._base_manager.filter(
            sponsors__id__startswith=SEEDED_ID_START
        ).distinct()
    )
    return records
