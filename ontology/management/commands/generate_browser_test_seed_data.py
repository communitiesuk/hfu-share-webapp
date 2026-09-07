from django.core.management.base import BaseCommand, CommandError

from hfurb_scripts.browser_test_seed.loader import browser_test_seeding_allowed


class Command(BaseCommand):
    help = (
        "Regenerate browser_tests/seed_data.json from the scenario definitions. "
        "Run locally whenever the scenarios change; never runs as part of seeding."
    )

    def handle(self, *args, **options):
        if not browser_test_seeding_allowed():
            raise CommandError("generate_browser_test_seed_data only runs locally")

        from hfurb_scripts.seeders.stages.seed_browser_test_la import (
            generate_browser_test_seed_data,
        )

        path, count = generate_browser_test_seed_data()
        self.stdout.write(f"Wrote {count} records to {path}")
