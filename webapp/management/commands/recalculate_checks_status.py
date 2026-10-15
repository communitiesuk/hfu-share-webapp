import argparse

from django.core.management.base import BaseCommand

from hfurb_scripts.recalculate_checks_status import (
    recalculate_checks_status,
)


class Command(BaseCommand):
    help = (
        "Recalculate the checks status on accommodation request "
        "marked as needing it recalulated (dry run by default)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Run without saving changes (default: True).",
        )

    def handle(self, *args, **options):
        recalculate_checks_status(options["dry_run"])
