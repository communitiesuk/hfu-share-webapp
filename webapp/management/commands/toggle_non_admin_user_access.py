from django.core.management.base import BaseCommand

from hfurb_scripts.toggle_non_admin_user_access import toggle_non_admin_user_access


class Command(BaseCommand):
    help = "Enable or disable non admin user access"

    def add_arguments(self, parser):
        parser.add_argument(
            "--disable",
            action="store_true",
            help="Disable the non admin user",
        )
        parser.add_argument(
            "--enable",
            action="store_true",
            help="Enable the non admin user",
        )

    def handle(self, *args, **options):
        toggle_non_admin_user_access(options["disable"], options["enable"])
