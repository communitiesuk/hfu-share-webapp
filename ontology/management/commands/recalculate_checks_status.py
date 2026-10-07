from django.core.management.base import BaseCommand

from hfurb_scripts.recalculate_checks_status import (
    recalculate_checks_status,
)


class Command(BaseCommand):
    help = (
        "Recalculate the checks status on accommodation request "
        "marked as needing it recalulated"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Commit changes to database, otherwise rollback after a dry run",
        )

    def handle(self, *args, **options):
        recalculate_checks_status(not options["commit"])
