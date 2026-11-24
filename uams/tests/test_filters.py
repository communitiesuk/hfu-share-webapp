from ontology.models import SponsorshipCertificationForm
from ontology.tests.factories import SponsorshipCertificationFormFactory
from test_utils.base import BaseTestCase
from uams.views import UamsFilter


class FilterUamsTestCase(BaseTestCase):
    def setUp(self):
        self.app1 = SponsorshipCertificationFormFactory(
            given_name="John",
            family_name="Doe",
            sponsor_date_of_birth="1980-05-15",
            created_at="2025-08-01T00:00:00Z",
        )
        self.app2 = SponsorshipCertificationFormFactory(
            given_name="Jane",
            family_name="Doe",
            sponsor_date_of_birth="1980-06-15",
            created_at="2025-09-01T00:00:00Z",
        )

    def _check_object_in_results(self, obj, results):
        return str(obj.pk) in [result.pk for result in results]

    def test_filter_by_sponsor_date_of_birth(self):
        filter_set = UamsFilter(
            queryset=SponsorshipCertificationForm.objects.all(),
            data={
                "sponsor_date_of_birth": "1980-05-01",
                "sponsor_date_of_birth_1": "1980-05-31",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 1)
        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertFalse(self._check_object_in_results(self.app2, results))

    def test_filter_by_created_at(self):
        filter_set = UamsFilter(
            queryset=SponsorshipCertificationForm.objects.all(),
            data={
                "created_at": "2025-08-15",
                "created_at_1": "2025-09-15",
            },
        )

        results = filter_set.qs
        self.assertEqual(len(results), 1)
        self.assertFalse(self._check_object_in_results(self.app1, results))
        self.assertTrue(self._check_object_in_results(self.app2, results))

    def test_filter_by_status(self):
        in_progress = SponsorshipCertificationFormFactory(
            uk_consent_form_status="Passed"
        )
        failed = SponsorshipCertificationFormFactory(uk_consent_form_status="Failed")

        filter_set = UamsFilter(
            queryset=SponsorshipCertificationForm.objects.all(),
            data={"status": ["UKVI checks in progress"]},
        )

        results = filter_set.qs
        self.assertEqual(len(results), 1)
        self.assertTrue(self._check_object_in_results(in_progress, results))
        self.assertFalse(self._check_object_in_results(failed, results))

    def test_filter_by_multiple_statuses(self):
        in_progress = SponsorshipCertificationFormFactory(
            uk_consent_form_status="Passed"
        )
        failed = SponsorshipCertificationFormFactory(uk_consent_form_status="Failed")

        filter_set = UamsFilter(
            queryset=SponsorshipCertificationForm.objects.all(),
            data={"status": ["UKVI checks in progress", "Status not recorded"]},
        )

        results = filter_set.qs
        self.assertEqual(len(results), 3)
        self.assertTrue(self._check_object_in_results(in_progress, results))
        self.assertTrue(self._check_object_in_results(self.app1, results))
        self.assertTrue(self._check_object_in_results(self.app2, results))
        self.assertFalse(self._check_object_in_results(failed, results))
