from django.test import SimpleTestCase

from accounts.enums import BROWSER_TEST_LTLA_NAMES
from hfurb_scripts.seeders.stages.seed_browser_test_la import BROWSER_TEST_ID_PREFIX

# The data pipelines exclude browser test records by these two conventions
# (see the writeback filters in hfurb-data-transforms), so a new browser test
# local authority or a changed id scheme must keep them or update the pipelines.
BROWSER_TEST_LTLA_NAME_MARKER = "(Browser test LTLA)"


class BrowserTestNamingConventionTestCase(SimpleTestCase):
    def test_every_browser_test_ltla_name_carries_the_marker(self):
        for name in BROWSER_TEST_LTLA_NAMES:
            with self.subTest(name):
                self.assertIn(BROWSER_TEST_LTLA_NAME_MARKER, name)

    def test_seeded_record_ids_start_with_the_browser_test_prefix(self):
        self.assertEqual(BROWSER_TEST_ID_PREFIX, "browser-test")
