from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from hfurb_scripts.browser_test_seed.loader import (
    browser_test_seeding_allowed,
    reset_browser_test_la,
    signals_muted,
)
from hfurb_scripts.browser_test_seed.records import wipe_browser_test_la_data


class Command(BaseCommand):
    help = "Reset the browser test local authority to the committed seed data file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what the wipe would delete, then roll back",
        )
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Reset the browser test data",
        )
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Wipe the browser test data",
        )

    def handle(self, *args, **options):
        if not browser_test_seeding_allowed():
            raise CommandError(
                "seed_browser_test_la only runs in dev or local environments"
            )

        if options["dry_run"]:
            with signals_muted(), transaction.atomic():
                wipe_browser_test_la_data()
                transaction.set_rollback(True)
            self.stdout.write("Dry run complete, nothing was deleted.")
            return

        if options["wipe"]:
            with signals_muted(), transaction.atomic():
                wipe_browser_test_la_data()
            self.stdout.write("Browser test data was wiped")
            return

        reset_browser_test_la()
