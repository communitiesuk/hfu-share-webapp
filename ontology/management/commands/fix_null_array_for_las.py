from django.core.management.base import BaseCommand

from hfurb_scripts.fix_null_array_for_las import (
    fix_null_array_for_las,
)


class Command(BaseCommand):
    help = "Fixes ARs where the LTLA or UTLA is a null array"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Commit changes to database, otherwise rollback after a dry run",
        )

    def handle(self, *args, **options):
        fix_null_array_for_las(not options["commit"])
