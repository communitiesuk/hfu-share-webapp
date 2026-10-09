from django.core.management.base import BaseCommand

from hfurb_scripts.suspend_inactive_users import (
    suspend_inactive_users,
)


class Command(BaseCommand):
    help = "Suspend users who have been inatcive for a certain period of time"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Commit changes to database, otherwise rollback after a dry run",
        )

    def handle(self, *args, **options):
        suspend_inactive_users(not options["commit"])
