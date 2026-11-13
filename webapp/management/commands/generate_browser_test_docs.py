import logging
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from hfurb_scripts.seeders.browser_test_docs import (
    DEFAULT_OUTPUT_PATH,
    render_browser_test_scenario_doc,
)
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    browser_test_seeding_allowed,
    seed_browser_test_la,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Seed the browser test local authority and regenerate "
        "browser_tests/seed_scenarios.md from the resulting data"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=str(DEFAULT_OUTPUT_PATH),
            help="Path to write the generated markdown to",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help=(
                "Do not write; compare the freshly rendered document against "
                "the file on disk and exit non-zero if they differ"
            ),
        )

    def handle(self, *args, **options):
        if not browser_test_seeding_allowed():
            raise CommandError(
                "generate_browser_test_docs only runs in dev or local environments"
            )

        if not os.getenv("SKIP_BROWSER_TEST_SEED"):
            logger.info("Seeding browser test LA before generating documentation")
            seed_browser_test_la()
        else:
            logger.info("Skipping seeding browser test LA")

        content = render_browser_test_scenario_doc()
        output_path = Path(options["output"])

        if options["check"]:
            existing = output_path.read_text() if output_path.exists() else None
            if existing == content:
                logger.info("%s is up to date", output_path)
                return
            raise CommandError(
                f"{output_path} is out of date; run "
                "`python manage.py generate_browser_test_docs` to regenerate it"
            )

        output_path.write_text(content)
        logger.info("Wrote %s", output_path)
