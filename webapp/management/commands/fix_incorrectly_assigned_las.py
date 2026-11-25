import argparse

from django.core.management.base import BaseCommand

from hfurb_scripts.fix_incorrectly_assigned_las import fix_incorrectly_assigned_las


class Command(BaseCommand):
    help = (
        "Updates the local authority on accommodations and visa applications "
        "listed in the manual data imports bucket (dry run by default)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Run without saving changes (default: True).",
        )

    def handle(self, *args, **options):
        fix_incorrectly_assigned_las(options["dry_run"])
