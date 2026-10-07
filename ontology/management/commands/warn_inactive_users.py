from django.core.management.base import BaseCommand

from hfurb_scripts.warn_inactive_users import (
    warn_inactive_users,
)


class Command(BaseCommand):
    help = (
        "Warn users who have been inatcive for a certain period of time that "
        "there account will be suspended"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Send messages to users, otherwise rollback after a dry run",
        )

    def handle(self, *args, **options):
        warn_inactive_users(not options["commit"])
