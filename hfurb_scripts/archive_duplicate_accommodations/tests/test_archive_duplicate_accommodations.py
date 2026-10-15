import os
from unittest import mock

import boto3
from django.db import DatabaseError
from moto import mock_aws

from deduplication.tests.factories import AccommodationDuplicateGroupFactory
from hfurb_scripts.archive_duplicate_accommodations import (
    DuplicateSet,
    get_records_to_process,
    run,
)
from hfurb_scripts.tests.base import BaseScriptTestCaseWithSession
from ontology.models import MvAccommodation, MvInteraction
from ontology.tests.factories import (
    DevCheckV2Factory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvVolunteerFactory,
)


def duplicate_sets(rows: list[list[str]]) -> list[DuplicateSet]:
    """
    Builds the records to process from lists of IDs, with the master first
    """
    return [
        DuplicateSet(f"ref-{index}", master_id, duplicate_ids)
        for index, (master_id, *duplicate_ids) in enumerate(rows)
    ]


@mock.patch("hfurb_scripts.archive_duplicate_accommodations.get_records_to_process")
class TestArchiveDuplicateAccommodations(BaseScriptTestCaseWithSession):
    def setUp(self):
        super().setUp()

        self.master = MvAccommodationFactory()
        self.duplicate = MvAccommodationFactory()
        self.other_duplicate = MvAccommodationFactory()
        self.not_in_list = MvAccommodationFactory()

    def run_script(self, dry_run=False):
        run(dry_run=dry_run)

    def is_archived(self, accommodation: MvAccommodation) -> bool:
        accommodation.refresh_from_db()
        return accommodation.is_archived

    def test_archives_duplicates_without_linked_records(self, mock_get_records):
        sponsor = MvVolunteerFactory()
        self.duplicate.hosts.add(sponsor)
        mock_get_records.return_value = duplicate_sets(
            [[self.master.id, self.duplicate.id, self.other_duplicate.id]]
        )

        self.run_script()

        self.assertFalse(self.is_archived(self.master))
        self.assertTrue(self.is_archived(self.duplicate))
        self.assertTrue(self.is_archived(self.other_duplicate))
        self.assertFalse(self.is_archived(self.not_in_list))
        self.assertIsNotNone(self.duplicate.archived_at)
        self.assertTrue(self.duplicate.edited_in_app)
        self.assertEqual(list(self.duplicate.hosts.all()), [sponsor])

    def test_skips_duplicates_with_linked_records(self, mock_get_records):
        def link_ar(accommodation):
            MvAccommodationRequestFactory(primary_accommodation=accommodation)

        def link_interaction(accommodation):
            MvInteraction.objects.create(linked_accommodation=accommodation)

        def link_check(accommodation):
            DevCheckV2Factory().accommodation.add(accommodation)

        def link_dedup_group(accommodation):
            AccommodationDuplicateGroupFactory(principal_record=accommodation)

        for link in [link_ar, link_interaction, link_check, link_dedup_group]:
            with self.subTest(link.__name__):
                master = MvAccommodationFactory()
                linked = MvAccommodationFactory()
                unlinked = MvAccommodationFactory()
                link(linked)
                mock_get_records.return_value = duplicate_sets(
                    [[master.id, linked.id, unlinked.id]]
                )

                self.run_script()

                self.assertFalse(self.is_archived(linked))
                self.assertTrue(self.is_archived(unlinked))

    def test_skips_duplicates_that_are_not_editable(self, mock_get_records):
        not_editable = MvAccommodationFactory()
        MvAccommodation.objects.filter(id=not_editable.id).update(is_editable=False)
        mock_get_records.return_value = duplicate_sets(
            [[self.master.id, not_editable.id, self.duplicate.id]]
        )

        self.run_script()

        self.assertFalse(self.is_archived(not_editable))
        self.assertTrue(self.is_archived(self.duplicate))

    def test_dry_run_does_not_change_anything(self, mock_get_records):
        mock_get_records.return_value = duplicate_sets(
            [[self.master.id, self.duplicate.id, self.other_duplicate.id]]
        )

        self.run_script(dry_run=True)

        self.assertFalse(self.is_archived(self.duplicate))
        self.assertFalse(self.is_archived(self.other_duplicate))

    def test_missing_duplicate_does_not_stop_others_being_archived(
        self, mock_get_records
    ):
        mock_get_records.return_value = duplicate_sets(
            [
                [self.master.id],
                [self.master.id, self.duplicate.id, "does-not-exist"],
            ]
        )

        self.run_script()

        self.assertFalse(self.is_archived(self.master))
        self.assertTrue(self.is_archived(self.duplicate))

    def test_lists_every_duplicate_not_archived_by_reason(self, mock_get_records):
        linked = MvAccommodationFactory()
        MvInteraction.objects.create(linked_accommodation=linked)
        not_editable = MvAccommodationFactory()
        MvAccommodation.objects.filter(id=not_editable.id).update(is_editable=False)
        already_archived = MvAccommodationFactory()
        MvAccommodation.objects.filter(id=already_archived.id).update(is_archived=True)
        failing = MvAccommodationFactory()
        mock_get_records.return_value = duplicate_sets(
            [
                [self.master.id, linked.id, not_editable.id, self.duplicate.id],
                [
                    self.not_in_list.id,
                    already_archived.id,
                    failing.id,
                    "does-not-exist",
                ],
            ]
        )
        original_save = MvAccommodation.save

        def fail_on_failing(accommodation, *args, **kwargs):
            if accommodation.id == failing.id:
                raise DatabaseError("Database down")
            original_save(accommodation, *args, **kwargs)

        with (
            mock.patch.object(MvAccommodation, "save", fail_on_failing),
            self.assertLogs(
                "hfurb_scripts.archive_duplicate_accommodations", level="INFO"
            ) as logs,
        ):
            self.run_script()

        summary = "\n".join(logs.output[-6:])
        self.assertIn("Accommodations: 1 archived, 5 not archived", summary)
        self.assertIn(f"1 not archived as it has linked records: {linked.id}", summary)
        self.assertIn(
            f"1 not archived as it is not editable: {not_editable.id}", summary
        )
        self.assertIn(
            f"1 not archived as it is already archived: {already_archived.id}", summary
        )
        self.assertIn(f"1 not archived as it failed to archive: {failing.id}", summary)
        self.assertIn("1 not archived as it was not found: does-not-exist", summary)


@mock.patch(
    "hfurb_scripts.archive_duplicate_accommodations.RECORDS_FILE_KEY", "records.csv"
)
@mock.patch(
    "hfurb_scripts.archive_duplicate_accommodations.RECORDS_BUCKET_NAME", "test-bucket"
)
class TestGetRecordsToProcess(BaseScriptTestCaseWithSession):
    @mock.patch.dict(
        os.environ, {"AWS_ENDPOINT_URL": "https://s3.eu-west-2.amazonaws.com"}
    )
    @mock_aws
    def test_returns_master_first_followed_by_its_duplicates(self):
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        s3.put_object(
            Bucket="test-bucket",
            Key="records.csv",
            Body=(
                "reference,id,ids_list\n"
                'ref-1,accommodation-1,"[""accommodation-1"",""accommodation-2"",'
                '""accommodation-3""]"\n'
                # Matches the real file, where the master is not always first
                "VNB3E9Y7,accommodation-80C7D3B4_BH10,"
                '"[""accommodation-CA158A27_BH10"",""accommodation-80C7D3B4_BH10""]"\n'
            ),
        )

        self.assertEqual(
            get_records_to_process(),
            [
                DuplicateSet(
                    "ref-1", "accommodation-1", ["accommodation-2", "accommodation-3"]
                ),
                DuplicateSet(
                    "VNB3E9Y7",
                    "accommodation-80C7D3B4_BH10",
                    ["accommodation-CA158A27_BH10"],
                ),
            ],
        )
