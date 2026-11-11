from django.test import TestCase

from ontology.models import SponsorshipCertificationForm
from ontology.tests.factories import SponsorshipCertificationFormFactory

PRE_APPROVAL_CHECK_FIELDS = [
    "uk_consent_form_status",
    "ukraine_consent_form_status",
    "sponsor_immigration_eligibility_status",
    "sponsor_household_security_checks_status",
    "sponsor_household_enhanced_dbs_status",
    "accommodation_exists_status",
    "accommodation_suitable_status",
    "sponsor_role_and_expectations_status",
    "sponsor_arrangements_suitable_status",
]


class SponsorshipCertificationFormPreApprovalCheckDefaultTests(TestCase):
    def test_new_application_has_no_checks_recorded(self):
        SponsorshipCertificationFormFactory(reference="SCF001")

        uam = SponsorshipCertificationForm.objects.get(reference="SCF001")

        for field in PRE_APPROVAL_CHECK_FIELDS:
            with self.subTest(field=field):
                self.assertIsNone(getattr(uam, field))

    def test_new_application_defaults_code_sent_to_sponsor_to_false(self):
        SponsorshipCertificationFormFactory(reference="SCF001")

        uam = SponsorshipCertificationForm.objects.get(reference="SCF001")

        self.assertIs(uam.sponsor_certification_code_emailed, False)
