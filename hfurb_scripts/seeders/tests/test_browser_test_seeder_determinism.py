import json
import random
import re
from unittest import mock

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.test import override_settings
from faker import Faker

from accounts.enums import (
    BROWSER_TEST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    GroupType,
)
from accounts.tests.factories import GroupFactory, UserFactory
from hfurb_scripts.seeders import helpers
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    BROWSER_TEST_ID_PREFIX,
    seed_browser_test_la,
)
from ontology.models import (
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    VisaApplication,
)
from test_utils.base import BaseTestCase

SNAPSHOT_MODELS = [
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    MvAccommodation,
    VisaApplication,
    DevCheckV2,
    ReassignmentRequest,
]


APP_MINTED_ID = re.compile(r"(person|sponsor|accommodation)-[0-9a-f-]{36}")


def _snapshot() -> str:
    records: list[dict] = []
    for model in SNAPSHOT_MODELS:
        queryset = model._base_manager.filter(
            pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-"
        ).order_by("pk")
        for record in serializers.serialize("python", queryset):
            for name, value in record["fields"].items():
                if isinstance(value, list):
                    record["fields"][name] = sorted(value, key=str)
            records.append(record)
    serialised = json.dumps(records, cls=DjangoJSONEncoder, sort_keys=True)
    return APP_MINTED_ID.sub(r"\1-<app-minted>", serialised)


def _drain_global_randomness(*args, **kwargs):
    random.random()
    Faker().name()
    return _original_create_mv_person(*args, **kwargs)


_original_create_mv_person = helpers.create_mv_person


@override_settings(ENVIRONMENT="dev")
class BrowserTestSeederDeterminismTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        group = GroupFactory(
            name=BROWSER_TEST_LA_GROUP_NAME,
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__utla_name="Hobbiton (Browser test UTLA)",
            groupinfo__da_name="England",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
        )
        UserFactory().groups.add(group)

    def test_reseeding_produces_identical_records(self):
        seed_browser_test_la()
        first = _snapshot()

        seed_browser_test_la()

        self.assertEqual(first, _snapshot())

    def test_seeding_is_isolated_from_the_global_random_generators(self):
        seed_browser_test_la()
        baseline = _snapshot()

        with mock.patch.object(
            helpers, "create_mv_person", side_effect=_drain_global_randomness
        ):
            seed_browser_test_la()

        self.assertEqual(
            baseline,
            _snapshot(),
            "draws from random.random() and the shared Faker generator during "
            "seeding must not change the seeded records",
        )
