from unittest import mock

from deduplication.models import AccommodationDuplicateGroup
from deduplication.tests.factories import AccommodationDuplicateGroupFactory
from hfurb_scripts.clean_up_duplicate_accommodations import AUTHOR, run
from hfurb_scripts.tests.base import BaseScriptTestCaseWithSession
from ontology.models import (
    MvAccommodation,
    MvInteraction,
    MvVolunteer,
)
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)


@mock.patch("hfurb_scripts.clean_up_duplicate_accommodations.get_records_to_process")
class TestCleanUpDuplicateAccommodations(BaseScriptTestCaseWithSession):
    def setUp(self):
        super().setUp()

        self.master = MvAccommodationFactory(is_principal=True)
        self.duplicate = MvAccommodationFactory(is_principal=True)
        self.other_duplicate = MvAccommodationFactory(is_principal=True)
        self.not_in_list = MvAccommodationFactory(is_principal=True)

    def run_script(self, dry_run=False):
        run(dry_run=dry_run)

    def exists(self, accommodation: MvAccommodation) -> bool:
        return MvAccommodation.objects_including_archived.filter(
            id=accommodation.id
        ).exists()

    def test_deletes_duplicates_nothing_depends_on(self, mock_get_records):
        sponsor = MvVolunteerFactory()
        self.duplicate.hosts.add(sponsor)
        mock_get_records.return_value = [
            [self.master.id, self.duplicate.id, self.other_duplicate.id]
        ]

        self.run_script()

        self.assertTrue(self.exists(self.master))
        self.assertFalse(self.exists(self.duplicate))
        self.assertFalse(self.exists(self.other_duplicate))
        self.assertTrue(self.exists(self.not_in_list))
        self.assertTrue(MvVolunteer.objects.filter(id=sponsor.id).exists())
        self.assertFalse(AccommodationDuplicateGroup.objects.exists())

    def test_deduplicates_duplicates_with_dependencies(self, mock_get_records):
        def link_ar(accommodation):
            MvAccommodationRequestFactory(
                primary_accommodation=accommodation,
                accommodation_id=[accommodation.id],
            )

        def link_interaction(accommodation):
            MvInteraction.objects.create(linked_accommodation=accommodation)

        def link_check(accommodation):
            DevCheckV2Factory().accommodation.add(accommodation)

        def link_dedup_group(accommodation):
            AccommodationDuplicateGroupFactory(principal_record=accommodation)

        for link in [
            link_ar,
            link_interaction,
            link_check,
            link_dedup_group,
        ]:
            with self.subTest(link.__name__):
                master = MvAccommodationFactory(is_principal=True)
                linked = MvAccommodationFactory(is_principal=True)
                unlinked = MvAccommodationFactory(is_principal=True)
                link(linked)
                mock_get_records.return_value = [[master.id, linked.id, unlinked.id]]

                self.run_script()

                self.assertFalse(self.exists(unlinked))
                group = AccommodationDuplicateGroup.objects.get(accommodations=linked)
                self.assertCountEqual(group.accommodations.all(), [master, linked])
                self.assertEqual(
                    group.principal_record.full_address, master.full_address
                )
                master.refresh_from_db()
                linked.refresh_from_db()
                self.assertFalse(master.is_principal)
                self.assertFalse(linked.is_principal)

    def test_deduplicate_moves_ar_to_new_principal(self, mock_get_records):
        ar = MvAccommodationRequestFactory(
            primary_accommodation=self.duplicate,
            accommodation_id=[self.duplicate.id],
        )
        mock_get_records.return_value = [[self.master.id, self.duplicate.id]]

        self.run_script()

        group = AccommodationDuplicateGroup.objects.get()
        ar.refresh_from_db()
        self.assertEqual(ar.primary_accommodation_id, group.principal_record_id)

    def test_dry_run_does_not_change_anything(self, mock_get_records):
        MvAccommodationRequestFactory(primary_accommodation=self.duplicate)
        mock_get_records.return_value = [
            [self.master.id, self.duplicate.id, self.other_duplicate.id]
        ]

        self.run_script(dry_run=True)

        self.assertTrue(self.exists(self.duplicate))
        self.assertTrue(self.exists(self.other_duplicate))
        self.assertFalse(AccommodationDuplicateGroup.objects.exists())
        self.master.refresh_from_db()
        self.assertTrue(self.master.is_principal)

    def test_skips_invalid_rows(self, mock_get_records):
        mock_get_records.return_value = [
            [],
            [self.master.id],
            [self.master.id, self.duplicate.id, "does-not-exist"],
        ]

        self.run_script()

        self.assertTrue(self.exists(self.master))
        self.assertTrue(self.exists(self.duplicate))

    def test_skips_row_needing_dedupe_with_non_principal_record(self, mock_get_records):
        # Already merged into another group, so can't be deleted or deduplicated
        already_merged = MvAccommodationFactory(is_principal=False)
        AccommodationDuplicateGroupFactory().accommodations.add(already_merged)
        mock_get_records.return_value = [
            [self.master.id, already_merged.id, self.duplicate.id]
        ]

        self.run_script()

        self.assertTrue(self.exists(already_merged))
        self.assertTrue(self.exists(self.duplicate))
        self.assertEqual(AccommodationDuplicateGroup.objects.count(), 1)

    @mock.patch.object(AccommodationDuplicateGroup, "deduplicate")
    def test_failed_row_is_rolled_back_and_next_row_runs(
        self, mock_deduplicate, mock_get_records
    ):
        mock_deduplicate.side_effect = Exception("Database down")
        MvAccommodationRequestFactory(primary_accommodation=self.duplicate)
        next_master = MvAccommodationFactory(is_principal=True)
        next_duplicate = MvAccommodationFactory(is_principal=True)
        mock_get_records.return_value = [
            [self.master.id, self.duplicate.id, self.other_duplicate.id],
            [next_master.id, next_duplicate.id],
        ]

        self.run_script()

        self.assertTrue(self.exists(self.other_duplicate))
        self.assertFalse(self.exists(next_duplicate))

    def test_deduplication_is_recorded_against_system(self, mock_get_records):
        ar = MvAccommodationRequestFactory(
            primary_accommodation=self.duplicate,
            accommodation_id=[self.duplicate.id],
        )
        mock_get_records.return_value = [[self.master.id, self.duplicate.id]]

        self.run_script()

        group = AccommodationDuplicateGroup.objects.get()
        ar.refresh_from_db()
        self.assertEqual(ar.last_modified_by, AUTHOR)
        self.assertEqual(group.principal_record.created_by, AUTHOR)
        interaction = MvInteraction.objects.get(linked_accommodation=self.duplicate)
        self.assertIsNone(interaction.created_by)
