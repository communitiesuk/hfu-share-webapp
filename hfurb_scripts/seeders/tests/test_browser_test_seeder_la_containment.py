from django.db.models import Model
from django.test import override_settings

from accounts.enums import BROWSER_TEST_LTLA_NAMES
from accounts.tests.factories import UserFactory
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    BROWSER_TEST_ID_PREFIX,
    seed_browser_test_la,
)
from hfurb_scripts.seeders.tests.helpers import create_browser_test_la_groups
from ontology.models import (
    ExportToolObject,
    MvAccommodation,
    MvAccommodationRequest,
    MvUkPostcode,
    VisaApplication,
)
from test_utils.base import BaseTestCase

LTLA_BEARING_MODELS: list[tuple[type[Model], str, bool]] = [
    (MvAccommodation, "ltla_name", False),
    (MvUkPostcode, "ltla_name", False),
    (VisaApplication, "ltla_name", False),
    (MvAccommodationRequest, "ltla_name", True),
    (ExportToolObject, "ltla_name", True),
]


@override_settings(ENVIRONMENT="dev")
class BrowserTestSeederLaContainmentTestCase(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        groups = create_browser_test_la_groups()
        UserFactory().groups.add(groups[0])
        seed_browser_test_la()

    def _ltla_names_outside_the_browser_test_las(
        self, model: type[Model], field: str, is_array: bool
    ) -> list[str]:
        allowed = set(BROWSER_TEST_LTLA_NAMES) | {None, ""}

        found: set[str] = set()
        for value in model._base_manager.filter(
            pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-"
        ).values_list(field, flat=True):
            if is_array:
                found.update(value or [])
            else:
                found.add(value)

        return sorted(found - allowed)

    def test_every_checked_model_actually_has_seeded_records(self):
        empty = [
            model.__name__
            for model, _, _ in LTLA_BEARING_MODELS
            if not model._base_manager.filter(
                pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-"
            ).exists()
        ]

        self.assertEqual(
            empty,
            [],
            "these models matched no seeded records, so the containment check "
            "is not covering them",
        )

    def test_the_seeder_writes_into_no_la_outside_the_browser_test_las(self):
        strays = {
            model.__name__: names
            for model, field, is_array in LTLA_BEARING_MODELS
            if (
                names := self._ltla_names_outside_the_browser_test_las(
                    model, field, is_array
                )
            )
        }

        self.assertEqual(
            strays,
            {},
            "Seeded records landed in a local authority outside "
            f"{BROWSER_TEST_LTLA_NAMES}. Real users in that authority can see "
            "them, because get_for_user only applies "
            "exclude_browser_test_records on its see-all branch. Either add "
            "the authority to BROWSER_TEST_LTLA_NAMES with a migration "
            "creating its group, or point the scenario at an existing browser "
            "test LA.",
        )

    def test_every_seeded_accommodation_carries_the_browser_test_utla(self):
        utla_names = set(
            MvAccommodation._base_manager.filter(
                pk__startswith=f"{BROWSER_TEST_ID_PREFIX}-"
            ).values_list("utla_name", flat=True)
        )

        self.assertEqual(
            utla_names - {None, ""},
            {"Hobbiton (Browser test UTLA)"},
            "seeded accommodations must sit under the browser test UTLA",
        )
