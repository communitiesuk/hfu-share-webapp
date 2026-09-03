from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    browser_test_seeding_allowed,
    seed_browser_test_la,
    wipe_browser_test_la_data,
)


class Command(BaseCommand):
    help = "Reset the browser test local authority to its fixed seeded dataset"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what the wipe would delete, then roll back",
        )
        parser.add_argument(
            "--wipe-only",
            action="store_true",
            help="Delete browser test local authority records without reseeding",
        )

    def handle(self, *args, **options):
        if not browser_test_seeding_allowed():
            raise CommandError(
                "seed_browser_test_la only runs in dev or local environments"
            )

        if options["dry_run"]:
            with transaction.atomic():
                wipe_browser_test_la_data()
                transaction.set_rollback(True)
            self.stdout.write("Dry run complete, nothing was deleted.")
            return

        if options["wipe_only"]:
            with transaction.atomic():
                wipe_browser_test_la_data()
            self.stdout.write("Browser test LA wiped.")
            return

        seed_browser_test_la()
