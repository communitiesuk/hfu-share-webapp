import argparse

from django.core.management.base import BaseCommand

from hfurb_scripts.archive_duplicate_accommodations import (
    archive_duplicate_accommodations,
)


class Command(BaseCommand):
    help = (
        "Archives duplicate accommodations listed in the manual data imports "
        "bucket that have no linked records (dry run by default)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Run without saving changes (default: True).",
        )

    def handle(self, *args, **options):
        archive_duplicate_accommodations(options["dry_run"])
