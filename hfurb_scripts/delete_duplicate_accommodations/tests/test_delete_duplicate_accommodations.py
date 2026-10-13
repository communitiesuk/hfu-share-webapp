from unittest import mock

from hfurb_scripts.delete_duplicate_accommodations import run
from hfurb_scripts.tests.base import BaseScriptTestCaseWithSession
from ontology.models import MvAccommodation
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
)


@mock.patch("hfurb_scripts.delete_duplicate_accommodations.get_records_to_delete")
class TestDeleteDuplicateAccommodations(BaseScriptTestCaseWithSession):
    def setUp(self):
        super().setUp()

        self.not_in_delete_list = MvAccommodationFactory()
        self.duplicate = MvAccommodationFactory()
        self.archived_duplicate = MvAccommodationFactory(is_archived=True)
        self.linked_duplicate = MvAccommodationFactory()
        MvAccommodationRequestFactory(accommodation_id=[self.linked_duplicate.id])

        self.records_to_delete = [
            self.duplicate.id,
            self.archived_duplicate.id,
            self.linked_duplicate.id,
            "does-not-exist",
        ]

    def assert_exists(self, accommodation: MvAccommodation, exists: bool):
        self.assertEqual(
            MvAccommodation.objects_including_archived.filter(
                id=accommodation.id
            ).exists(),
            exists,
        )

    def test_dry_run_does_not_delete_anything(self, mock_get_records):
        mock_get_records.return_value = self.records_to_delete

        run()

        self.assert_exists(self.not_in_delete_list, True)
        self.assert_exists(self.duplicate, True)
        self.assert_exists(self.archived_duplicate, True)
        self.assert_exists(self.linked_duplicate, True)

    def test_run_deletes_unlinked_records(self, mock_get_records):
        mock_get_records.return_value = self.records_to_delete

        run(dry_run=False)

        self.assert_exists(self.not_in_delete_list, True)
        self.assert_exists(self.duplicate, False)
        self.assert_exists(self.archived_duplicate, False)
        self.assert_exists(self.linked_duplicate, True)

