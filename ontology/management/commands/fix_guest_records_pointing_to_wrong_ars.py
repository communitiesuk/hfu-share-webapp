from django.core.management.base import BaseCommand

from hfurb_scripts.fix_guest_records_pointing_to_wrong_ars import (
    fix_guest_records_pointing_to_wrong_ars,
)


class Command(BaseCommand):
    help = "Fixes ARs where the linked guests and the gustes linked AR does not match"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Commit changes to database, otherwise rollback after a dry run",
        )

    def handle(self, *args, **options):
        fix_guest_records_pointing_to_wrong_ars(not options["commit"])
