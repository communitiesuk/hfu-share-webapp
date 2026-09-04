from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from accounts.enums import BROWSER_TEST_LTLA_NAMES
from hfurb_scripts.seeders.stages.seed_browser_test_la import (
    AR_SCENARIOS,
    BROWSER_TEST_ID_PREFIX,
    browser_test_seeding_allowed,
)
from ontology.models import (
    DevCheckV2,
    MvAccommodation,
    MvAccommodationRequest,
    MvGroup,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingNotification,
    VisaApplication,
    VisaInformationRequest,
)


class Command(BaseCommand):
    help = (
        "Print the factual (DB-derived) content of browser_tests/"
        "seed_scenarios.md - ids, names, titles, addresses - after a "
        "seed_browser_test_la run, so the doc can be checked/patched "
        "against what the seeder actually produces."
    )

    def handle(self, *args, **options):
        if not browser_test_seeding_allowed():
            raise CommandError(
                "This command only runs in dev or local environments"
            )

        ltla_name = BROWSER_TEST_LTLA_NAMES[0]
        prefix = BROWSER_TEST_ID_PREFIX

        self.stdout.write("## Accommodation request scenarios\n")
        self.stdout.write("| # | AR id | Title | Checks status | Guest visa statuses |")
        self.stdout.write("| --- | --- | --- | --- | --- |")
        for index, scenario in enumerate(AR_SCENARIOS):
            ar_id = f"{prefix}-ar-{index + 1:05d}"
            ar = MvAccommodationRequest.objects.filter(id=ar_id).first()
            title = ar.title if ar else "MISSING"
            visa_statuses = ", ".join(scenario["visa_statuses"])
            self.stdout.write(
                f"| {index + 1} | {ar_id} | {title} | "
                f"{scenario['checks_status'].label} | {visa_statuses} |"
            )

        self.stdout.write("\n## Special scenario accommodation requests\n")
        self.stdout.write("| AR id | Title |")
        self.stdout.write("| --- | --- |")
        for ar in MvAccommodationRequest.objects.filter(
            id__startswith=f"{prefix}-ar-"
        ).exclude(
            id__in=[f"{prefix}-ar-{i + 1:05d}" for i in range(len(AR_SCENARIOS))]
        ).order_by("id"):
            self.stdout.write(f"| {ar.id} | {ar.title} |")

        self.stdout.write("\n## Guests (MvPerson)\n")
        self.stdout.write("| Id | Name | Visa status | AR |")
        self.stdout.write("| --- | --- | --- | --- |")
        for person in MvPerson.objects.filter(id__startswith=f"{prefix}-").order_by(
            "id"
        ):
            self.stdout.write(
                f"| {person.id} | {person.get_full_name()} | {person.visa_status} | "
                f"{person.accommodation_request_id or ''} |"
            )

        self.stdout.write("\n## Sponsors (MvVolunteer)\n")
        self.stdout.write("| Id | Name | AR(s) |")
        self.stdout.write("| --- | --- | --- |")
        for sponsor in MvVolunteer.objects.filter(id__startswith=f"{prefix}-").order_by(
            "id"
        ):
            ars = MvAccommodationRequest.objects.filter(
                sponsor_id__contains=[sponsor.id]
            ).order_by("id")
            ar_ids = ", ".join(ar.id for ar in ars)
            self.stdout.write(f"| {sponsor.id} | {sponsor.full_name} | {ar_ids} |")

        self.stdout.write("\n## Accommodations (MvAccommodation)\n")
        self.stdout.write("| Id | Address | LA | AR(s) |")
        self.stdout.write("| --- | --- | --- | --- |")
        for accommodation in MvAccommodation.objects.filter(
            id__startswith=f"{prefix}-"
        ).order_by("id"):
            ars = MvAccommodationRequest.objects.filter(
                accommodation_id__contains=[accommodation.id]
            ).order_by("id")
            ar_ids = ", ".join(ar.id for ar in ars)
            address = accommodation.full_address.replace("\n", " ")
            self.stdout.write(
                f"| {accommodation.id} | {address} | {accommodation.ltla_name} | "
                f"{ar_ids} |"
            )

        self.stdout.write("\n## Groups (MvGroup)\n")
        self.stdout.write("| Id | Title |")
        self.stdout.write("| --- | --- |")
        for group in MvGroup.objects.filter(id__startswith=f"{prefix}-").order_by(
            "id"
        ):
            self.stdout.write(f"| {group.id} | {group.title} |")

        self.stdout.write("\n## Visa applications\n")
        self.stdout.write("| Id | Applicant | Visa status | Unique application number |")
        self.stdout.write("| --- | --- | --- | --- |")
        for visa_application in VisaApplication.objects.filter(
            visa_application_id__startswith=f"{prefix}-"
        ).order_by("visa_application_id"):
            uan = visa_application.application_unique_application_number
            self.stdout.write(
                f"| {visa_application.visa_application_id} | "
                f"{visa_application.Q44g_full_name} | "
                f"{visa_application.visa_status} | {uan} |"
            )

        self.stdout.write("\n## Checks (DevCheckV2)\n")
        self.stdout.write("| Id | Type | Status | Failure reason | AR(s) |")
        self.stdout.write("| --- | --- | --- | --- | --- |")
        for check in DevCheckV2.objects.filter(id__startswith=f"{prefix}-").order_by(
            "id"
        ):
            ars = check.AR.all().order_by("id")
            ar_ids = ", ".join(ar.id for ar in ars)
            self.stdout.write(
                f"| {check.id} | {check.check_type} | {check.check_status or ''} | "
                f"{check.get_check_subtype_label()} | {ar_ids} |"
            )

        self.stdout.write("\n## Safeguarding notifications\n")
        self.stdout.write("| Id | AR | Check |")
        self.stdout.write("| --- | --- | --- |")
        for notification in SafeguardingNotification.objects.filter(
            ar__ltla_name__overlap=[ltla_name]
        ).order_by("id"):
            self.stdout.write(
                f"| {notification.id} | {notification.ar_id} | "
                f"{notification.dev_check_v2_id or ''} |"
            )

        self.stdout.write("\n## Reassignment requests\n")
        self.stdout.write("| Id | Outcome | Destination LA | AR |")
        self.stdout.write("| --- | --- | --- | --- |")
        for reassignment in ReassignmentRequest.objects.filter(
            Q(source_ltla_name__overlap=[ltla_name])
            | Q(destination_ltla_name=ltla_name)
        ).order_by("created_at"):
            self.stdout.write(
                f"| {reassignment.pk} | {reassignment.outcome} | "
                f"{reassignment.destination_ltla_name} | "
                f"{reassignment.accommodation_request_id} |"
            )

        self.stdout.write("\n## Visa information request records\n")
        self.stdout.write("| Id | Status | Visa application | Title |")
        self.stdout.write("| --- | --- | --- | --- |")
        for vir in VisaInformationRequest.objects.filter(
            visa_information_request_id__startswith=f"{prefix}-"
        ).order_by("visa_information_request_id"):
            self.stdout.write(
                f"| {vir.visa_information_request_id} | {vir.request_status} | "
                f"{vir.visa_application_id} | {vir.request_title} |"
            )
