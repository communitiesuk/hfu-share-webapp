from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.enums import (
    BROWSER_TEST_LA_GROUP_NAME,
    BROWSER_TEST_LTLA_NAMES,
    GroupType,
)
from accounts.tests.factories import GroupFactory
from hfurb_scripts.seeders.helpers import build_complete_accommodation_scenario
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    BROWSER_TEST_ID_PREFIX,
)
from ontology.models import (
    MvAccommodationRequest,
    MvPerson,
    VisaApplication,
)
from ontology.tests.factories import MvAccommodationRequestFactory


class SeedBrowserTestLaCommandTestCase(TestCase):
    def setUp(self):
        GroupFactory(
            name=BROWSER_TEST_LA_GROUP_NAME,
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
        )

    @override_settings(ENVIRONMENT="production", DEBUG=False)
    def test_refuses_to_run_outside_dev_environments(self):
        pre_existing_ar = MvAccommodationRequestFactory(
            ltla_name=[BROWSER_TEST_LTLA_NAMES[0]]
        )

        with self.assertRaises(CommandError):
            call_command("seed_browser_test_la")

        self.assertTrue(
            MvAccommodationRequest.objects.filter(pk=pre_existing_ar.pk).exists(),
            "the command must refuse before wiping anything",
        )

    @override_settings(ENVIRONMENT="dev")
    def test_dry_run_leaves_the_database_unchanged(self):
        build_complete_accommodation_scenario(
            num_guests=1,
            ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            id_prefix=BROWSER_TEST_ID_PREFIX,
            make_uam=False,
        )
        counts_before = (
            MvAccommodationRequest.objects.count(),
            MvPerson.objects.count(),
            VisaApplication.objects.count(),
        )

        call_command("seed_browser_test_la", "--dry-run")

        counts_after = (
            MvAccommodationRequest.objects.count(),
            MvPerson.objects.count(),
            VisaApplication.objects.count(),
        )
        self.assertEqual(
            counts_before,
            counts_after,
            "a dry run must report the wipe without deleting anything",
        )
