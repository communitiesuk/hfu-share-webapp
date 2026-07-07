from django.test import TestCase

from webapp.constants import visa_status_list_ordered
from webapp.views import combine_visa_statuses


class VisaStatusTest(TestCase):
    def assert_combine_visa_statuses(self, statuses: list[str], expected: str | None):
        self.assertEqual(combine_visa_statuses(statuses).name, expected)

    def test_combine_visa_no_statuses(self):
        """Empty or unknown statuses combine to None"""
        self.assert_combine_visa_statuses([], None)
        self.assert_combine_visa_statuses(["Unknown"], None)

    def test_combine_visa_single_or_same(self):
        """Single status or multiple identical statuses combine to the same status"""
        self.assert_combine_visa_statuses(["Issued"], "Issued")
        self.assert_combine_visa_statuses(["Issued", "Issued"], "Issued")
        self.assert_combine_visa_statuses(["Issued", "Issued", "Issued"], "Issued")
        self.assert_combine_visa_statuses(["Pending"], "Pending")
        self.assert_combine_visa_statuses(["Pending", "Pending"], "Pending")
        self.assert_combine_visa_statuses(["Pending", "Pending", "Pending"], "Pending")
        self.assert_combine_visa_statuses(["Confirmed"], "Confirmed")
        self.assert_combine_visa_statuses(["Confirmed", "Confirmed"], "Confirmed")
        self.assert_combine_visa_statuses(
            ["Confirmed", "Confirmed", "Confirmed"], "Confirmed"
        )

    def test_combine_some_issued(self):
        """Issued combines with any other status to 'Some issued'"""
        other_statuses = [
            "Arrived",
            "Confirmed",
            "Flow Visa Pending",
            "Pending",
            "Refused",
            "Withdrawn",
            "Lapsed",
            "Missing Application",
        ]
        for status in other_statuses:
            self.assert_combine_visa_statuses(["Issued", status], "Some issued")
            self.assert_combine_visa_statuses([status, "Issued"], "Some issued")

        self.assert_combine_visa_statuses(
            ["Issued", "Confirmed", "Confirmed"], "Some issued"
        )
        self.assert_combine_visa_statuses(
            ["Issued", "Issued", "Confirmed"], "Some issued"
        )
        self.assert_combine_visa_statuses(
            ["Issued", "Confirmed", "Issued", "Confirmed"], "Some issued"
        )

    def test_combine_other_combinations(self):
        """
        Other combinations of statuses combine to the least-progress status,
        or rejection type
        """
        self.assert_combine_visa_statuses(["Confirmed", "Pending"], "Pending")
        self.assert_combine_visa_statuses(["Confirmed", "Arrived"], "Confirmed")
        self.assert_combine_visa_statuses(["Pending", "Arrived"], "Pending")
        self.assert_combine_visa_statuses(
            ["Pending", "Confirmed", "Pending"], "Pending"
        )
        self.assert_combine_visa_statuses(
            ["Pending", "Confirmed", "Refused"], "Refused"
        )

    def test_ordered_status_list(self):
        self.assertEqual(
            [status.name for status in visa_status_list_ordered],
            [
                "Missing Application",
                "Pending",
                "Confirmed",
                "Issued",
                "Arrived",
                "Withdrawn",
                "Refused",
                "Lapsed",
                "Flow Visa Pending",
            ],
        )
