from unittest.mock import Mock

from django.test import TestCase

from ontology.actions.reassignment_request_actions import fill_missing_ltla_utla
from ontology.models.ReassignmentRequest import ReassignmentRequest


class FillMissingLtlaUtlaActionTest(TestCase):
    def setUp(self):
        self.modeladmin = Mock()
        self.request = Mock()
        self.modeladmin.message_user = Mock()

    def test_source_country_scotland_fills_source_ltla(self):
        req = ReassignmentRequest.objects.create(
            id="1",
            source_country=["Scotland"],
            source_ltla_name=None,
            viewer_groups=[
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-GENERAL-ALL data",
                "team-DLUHC-ontology-admins",
                "team-DLUHC-analysts",
                "exela-DLUHC-members",
            ],
        )
        fill_missing_ltla_utla(
            self.modeladmin, self.request, ReassignmentRequest.objects.filter(id="1")
        )
        req.refresh_from_db()
        self.assertEqual(req.source_ltla_name, ["Aberdeen City"])

    def test_destination_country_wales_fills_destination_ltla(self):
        req = ReassignmentRequest.objects.create(
            id="2",
            destination_country="Wales",
            destination_ltla_name=None,
            viewer_groups=[
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-GENERAL-ALL data",
                "team-DLUHC-ontology-admins",
                "team-DLUHC-analysts",
                "exela-DLUHC-members",
            ],
        )
        fill_missing_ltla_utla(
            self.modeladmin, self.request, ReassignmentRequest.objects.filter(id="2")
        )
        req.refresh_from_db()
        self.assertEqual(req.destination_ltla_name, "Cardiff")

    def test_viewer_groups_fills_source_ltla(self):
        req = ReassignmentRequest.objects.create(
            id="3",
            source_country=None,
            source_ltla_name=None,
            destination_ltla_name="Bristol",
            viewer_groups=[
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-GENERAL-ALL data",
                "team-DLUHC-ontology-admins",
                "team-DLUHC-analysts",
                "exela-DLUHC-members",
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-LTLA-Havant",
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-LTLA-Bristol",
            ],
        )
        fill_missing_ltla_utla(
            self.modeladmin, self.request, ReassignmentRequest.objects.filter(id="3")
        )
        req.refresh_from_db()
        self.assertEqual(req.source_ltla_name, ["Havant"])

    def test_viewer_groups_fills_destination_ltla(self):
        req = ReassignmentRequest.objects.create(
            id="4",
            destination_country=None,
            destination_ltla_name=None,
            source_ltla_name=["Havant"],
            viewer_groups=[
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-GENERAL-ALL data",
                "team-DLUHC-ontology-admins",
                "team-DLUHC-analysts",
                "exela-DLUHC-members",
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-LTLA-Havant",
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-LTLA-Bristol",
            ],
        )
        fill_missing_ltla_utla(
            self.modeladmin, self.request, ReassignmentRequest.objects.filter(id="4")
        )
        req.refresh_from_db()
        self.assertEqual(req.destination_ltla_name, "Bristol")

    def test_excluded_viewer_groups_does_not_fill(self):
        req = ReassignmentRequest.objects.create(
            id="5",
            source_country=None,
            source_ltla_name=None,
            destination_ltla_name=None,
            viewer_groups=[
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-GENERAL-ALL data",
                "team-DLUHC-ontology-admins",
                "team-DLUHC-analysts",
                "exela-DLUHC-members",
            ],
        )
        fill_missing_ltla_utla(
            self.modeladmin, self.request, ReassignmentRequest.objects.filter(id="5")
        )
        req.refresh_from_db()
        self.assertIsNone(req.source_ltla_name)
        self.assertIsNone(req.destination_ltla_name)

    def test_no_country_no_valid_viewer_group_does_not_fill(self):
        req = ReassignmentRequest.objects.create(
            id="6",
            source_country=None,
            source_ltla_name=None,
            destination_ltla_name=None,
            viewer_groups=[
                "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-GENERAL-ALL data",
                "team-DLUHC-ontology-admins",
                "team-DLUHC-analysts",
                "exela-DLUHC-members",
            ],
        )
        fill_missing_ltla_utla(
            self.modeladmin, self.request, ReassignmentRequest.objects.filter(id="6")
        )
        req.refresh_from_db()
        self.assertIsNone(req.source_ltla_name)
        self.assertIsNone(req.destination_ltla_name)
