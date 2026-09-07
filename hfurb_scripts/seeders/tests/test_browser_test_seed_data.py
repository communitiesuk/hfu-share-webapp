import json
import tempfile
from pathlib import Path

from django.core.serializers.json import DjangoJSONEncoder
from django.test import override_settings

from accounts.enums import (
    BROWSER_TEST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    GroupType,
)
from accounts.tests.factories import GroupFactory, UserFactory
from hfurb_scripts.browser_test_seed.loader import (
    get_browser_test_author,
    read_seed_data,
    reset_browser_test_la,
)
from hfurb_scripts.browser_test_seed.records import (
    collect_browser_test_records,
)
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    _serialise_browser_test_records,
    generate_browser_test_seed_data,
)
from test_utils.base import BaseTestCase


def _committed_seed_data() -> list[dict]:
    return read_seed_data()


def _as_json(records: list[dict]) -> list[dict]:
    return json.loads(json.dumps(records, cls=DjangoJSONEncoder, sort_keys=True))


@override_settings(ENVIRONMENT="dev")
class BrowserTestSeedDataTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        browser_test_group = GroupFactory(
            name=BROWSER_TEST_LA_GROUP_NAME,
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__utla_name="Hobbiton (Browser test UTLA)",
            groupinfo__da_name="England",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
        )
        user = UserFactory()
        user.groups.add(browser_test_group)

    def test_loader_reproduces_the_committed_seed_data_exactly(self):
        committed = _committed_seed_data()

        loaded_count = reset_browser_test_la()

        self.assertEqual(loaded_count, len(committed))
        self.assertEqual(
            sum(queryset.count() for _, queryset in collect_browser_test_records()),
            len(committed),
            "every loaded record must be within the wipe's reach",
        )
        loaded = _as_json(_serialise_browser_test_records(get_browser_test_author()))
        self.assertEqual(
            loaded,
            committed,
            "the database after loading must serialise back to the seed file",
        )

    def test_committed_seed_data_matches_the_scenario_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_browser_test_seed_data(Path(tmp))

            regenerated = read_seed_data(Path(tmp))

        self.assertEqual(
            regenerated,
            _committed_seed_data(),
            "scenario definitions changed: run "
            "`python manage.py generate_browser_test_seed_data` and commit the file",
        )
