from accounts.models import User
from ontology.mixins import DaViewerGroupNames
from ontology.models import ExportToolObject
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import (
    ExportToolObjectFactory,
    MvAccommodationFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import get_user_with_groups, get_user_with_no_access


class ExportToolObjectPermissionsTestCase(LocalAuthorityBaseTestCaseMixin):
    def assert_get_for_user_returns(self, user: User, requests: list[ExportToolObject]):
        return self.assertQuerySetEqual(
            ExportToolObject.objects.get_for_user(user).order_by("pk"),
            sorted(list({str(obj) for obj in requests})),
            transform=str,
        )

    def setUp(self):
        super().setUp()

        self.ltla_one_a_sponsor = MvVolunteerFactory()
        self.ltla_one_b_sponsor = MvVolunteerFactory()
        self.ltla_two_a_sponsor = MvVolunteerFactory()
        self.no_accommodation_sponsor = MvVolunteerFactory()
        self.accommodation_with_no_la_sponsor = MvVolunteerFactory()

        self.ltla_one_a_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_one_a_name,
            utla_name=self.utla_one_name,
        )
        self.ltla_one_a_accommodation.hosts.set([self.ltla_one_a_sponsor])

        self.ltla_one_b_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_one_b_name,
            utla_name=self.utla_one_name,
        )
        self.ltla_one_b_accommodation.hosts.set([self.ltla_one_b_sponsor])

        self.ltla_two_a_accommodation = MvAccommodationFactory(
            ltla_name=self.ltla_two_a_name,
            utla_name=self.utla_one_name,
        )
        self.ltla_two_a_accommodation.hosts.set([self.ltla_two_a_sponsor])

        self.no_la_accommodation = MvAccommodationFactory(
            ltla_name=None,
            utla_name=None,
        )
        self.no_la_accommodation.hosts.set([self.accommodation_with_no_la_sponsor])

        self.ltla_one_a_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.ltla_one_a_sponsor.pk,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.ltla_one_a_missing_utla_name_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.ltla_one_a_sponsor.pk,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.ltla_one_a_multi_ltla_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name, self.ltla_two_a_name],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.ltla_one_a_sponsor.pk,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.ltla_one_a_multi_utla_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name, self.utla_two_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.ltla_one_a_sponsor.pk,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.ltla_one_a_ltla_one_b_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.ltla_one_b_sponsor.pk,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.ltla_two_a_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_two_a_name],
            utla_name=[self.utla_two_name],
            rematched_host_id=self.ltla_two_a_sponsor.pk,
            sponsor_id=self.ltla_two_a_sponsor.pk,
            accommodation_id=self.ltla_two_a_accommodation.pk,
        )

        self.ltla_two_a_ltla_one_b_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_two_a_name],
            utla_name=[self.utla_two_name],
            rematched_host_id=self.ltla_one_b_sponsor.pk,
            sponsor_id=self.ltla_two_a_sponsor.pk,
            accommodation_id=self.ltla_two_a_accommodation.pk,
        )

        self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object = (
            ExportToolObjectFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[self.utla_two_name],
                rematched_host_id=self.ltla_two_a_sponsor.pk,
                sponsor_id=self.ltla_one_b_sponsor.pk,
                accommodation_id=self.ltla_two_a_accommodation.pk,
            )
        )

        self.sponsor_with_no_accommodation_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.no_accommodation_sponsor.pk,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.accommodation_with_no_la_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.no_accommodation_sponsor.pk,
            accommodation_id=self.no_la_accommodation.pk,
        )

        self.accommodation_with_no_la_sponsor_case_export_tool_object = (
            ExportToolObjectFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[self.utla_one_name],
                rematched_host_id=self.ltla_one_a_sponsor.pk,
                sponsor_id=self.accommodation_with_no_la_sponsor.pk,
                accommodation_id=self.ltla_one_a_accommodation.pk,
            )
        )

        self.accommodation_with_no_la_rematched_host_case_export_tool_object = (
            ExportToolObjectFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[self.utla_one_name],
                rematched_host_id=self.accommodation_with_no_la_sponsor.pk,
                sponsor_id=self.ltla_one_a_sponsor.pk,
                accommodation_id=self.ltla_one_a_accommodation.pk,
            )
        )

        self.ltla_one_a_missing_accommodation_export_tool_object_null = (
            ExportToolObjectFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[self.utla_one_name],
                rematched_host_id=self.ltla_one_a_sponsor.pk,
                sponsor_id=self.ltla_one_a_sponsor.pk,
                accommodation_id=None,
            )
        )

        self.ltla_one_a_missing_accommodation_export_tool_object_blank = (
            ExportToolObjectFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[self.utla_one_name],
                rematched_host_id=self.ltla_one_a_sponsor.pk,
                sponsor_id=self.ltla_one_a_sponsor.pk,
                accommodation_id="",
            )
        )

        self.ltla_one_a_missing_sponsor_tool_object_null = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=None,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.ltla_one_a_missing_sponsor_tool_object_blank = ExportToolObjectFactory(
            ltla_name=[self.ltla_one_a_name],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id="",
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.ltla_one_a_missing_rematched_host_tool_object_null = (
            ExportToolObjectFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[self.utla_one_name],
                rematched_host_id=None,
                sponsor_id=self.ltla_one_a_sponsor.pk,
                accommodation_id=self.ltla_one_a_accommodation.pk,
            )
        )

        self.ltla_one_a_missing_rematched_host_tool_object_blank = (
            ExportToolObjectFactory(
                ltla_name=[self.ltla_one_a_name],
                utla_name=[self.utla_one_name],
                rematched_host_id="",
                sponsor_id=self.ltla_one_a_sponsor.pk,
                accommodation_id=self.ltla_one_a_accommodation.pk,
            )
        )

        self.utla_one_export_tool_object = ExportToolObjectFactory(
            ltla_name=[],
            utla_name=[self.utla_one_name],
            rematched_host_id=self.ltla_one_a_sponsor.pk,
            sponsor_id=self.ltla_one_a_sponsor.pk,
            accommodation_id=self.ltla_one_a_accommodation.pk,
        )

        self.other_da_export_tool_object = ExportToolObjectFactory(
            ltla_name=[self.ltla_other_da_name]
        )

        self.da_england_export_tool_object = ExportToolObjectFactory(
            ltla_name=[],
            utla_name=[],
            viewer_group_names=[DaViewerGroupNames.ENGLAND],
        )

        self.user_with_ltla_one_a_export_tool_objects = [
            self.ltla_one_a_export_tool_object,
            self.ltla_one_a_missing_utla_name_export_tool_object,
            self.ltla_one_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_ltla_export_tool_object,
            self.ltla_one_a_multi_utla_export_tool_object,
            self.ltla_one_a_missing_accommodation_export_tool_object_null,
            self.ltla_one_a_missing_accommodation_export_tool_object_blank,
            self.ltla_one_a_missing_sponsor_tool_object_null,
            self.ltla_one_a_missing_sponsor_tool_object_blank,
            self.ltla_one_a_missing_rematched_host_tool_object_null,
            self.ltla_one_a_missing_rematched_host_tool_object_blank,
            self.sponsor_with_no_accommodation_export_tool_object,
            self.accommodation_with_no_la_sponsor_case_export_tool_object,
            self.accommodation_with_no_la_rematched_host_case_export_tool_object,
            self.accommodation_with_no_la_export_tool_object,
        ]

        self.user_with_ltla_one_b_export_tool_objects = []

        self.user_with_ltla_two_a_export_tool_objects = [
            self.ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_ltla_export_tool_object,
            self.ltla_two_a_ltla_one_b_export_tool_object,
        ]

        self.user_with_ltla_one_a_ltla_one_b_export_tool_objects = [
            self.ltla_one_a_export_tool_object,
            self.ltla_one_a_missing_utla_name_export_tool_object,
            self.ltla_one_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_ltla_export_tool_object,
            self.ltla_one_a_multi_utla_export_tool_object,
            self.ltla_one_a_missing_accommodation_export_tool_object_null,
            self.ltla_one_a_missing_accommodation_export_tool_object_blank,
            self.ltla_one_a_missing_sponsor_tool_object_null,
            self.ltla_one_a_missing_sponsor_tool_object_blank,
            self.ltla_one_a_missing_rematched_host_tool_object_null,
            self.ltla_one_a_missing_rematched_host_tool_object_blank,
            self.sponsor_with_no_accommodation_export_tool_object,
            self.accommodation_with_no_la_sponsor_case_export_tool_object,
            self.accommodation_with_no_la_rematched_host_case_export_tool_object,
            self.accommodation_with_no_la_export_tool_object,
        ]

        self.user_with_ltla_one_a_ltla_one_b_ltla_two_a_export_tool_objects = [
            self.ltla_one_a_export_tool_object,
            self.ltla_one_a_missing_utla_name_export_tool_object,
            self.ltla_one_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_ltla_export_tool_object,
            self.ltla_two_a_export_tool_object,
            self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_utla_export_tool_object,
            self.ltla_two_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_missing_accommodation_export_tool_object_null,
            self.ltla_one_a_missing_accommodation_export_tool_object_blank,
            self.ltla_one_a_missing_sponsor_tool_object_null,
            self.ltla_one_a_missing_sponsor_tool_object_blank,
            self.ltla_one_a_missing_rematched_host_tool_object_null,
            self.ltla_one_a_missing_rematched_host_tool_object_blank,
            self.sponsor_with_no_accommodation_export_tool_object,
            self.accommodation_with_no_la_sponsor_case_export_tool_object,
            self.accommodation_with_no_la_rematched_host_case_export_tool_object,
            self.accommodation_with_no_la_export_tool_object,
        ]

        self.user_with_utla_one_export_tool_objects = [
            self.ltla_one_a_export_tool_object,
            self.ltla_one_a_missing_utla_name_export_tool_object,
            self.ltla_one_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_ltla_export_tool_object,
            self.ltla_one_a_multi_utla_export_tool_object,
            self.ltla_one_a_missing_accommodation_export_tool_object_null,
            self.ltla_one_a_missing_accommodation_export_tool_object_blank,
            self.ltla_one_a_missing_sponsor_tool_object_null,
            self.ltla_one_a_missing_sponsor_tool_object_blank,
            self.ltla_one_a_missing_rematched_host_tool_object_null,
            self.ltla_one_a_missing_rematched_host_tool_object_blank,
            self.utla_one_export_tool_object,
            self.sponsor_with_no_accommodation_export_tool_object,
            self.accommodation_with_no_la_sponsor_case_export_tool_object,
            self.accommodation_with_no_la_rematched_host_case_export_tool_object,
            self.accommodation_with_no_la_export_tool_object,
        ]

        self.user_with_utla_two_export_tool_objects = [
            self.ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_ltla_export_tool_object,
            self.ltla_two_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_utla_export_tool_object,
        ]

        self.user_with_da_main_export_tool_objects = [
            self.ltla_one_a_export_tool_object,
            self.ltla_one_a_missing_utla_name_export_tool_object,
            self.ltla_one_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_multi_ltla_export_tool_object,
            self.ltla_one_a_ltla_one_b_ltla_two_a_export_tool_object,
            self.ltla_two_a_export_tool_object,
            self.ltla_one_a_multi_utla_export_tool_object,
            self.ltla_two_a_ltla_one_b_export_tool_object,
            self.ltla_one_a_missing_accommodation_export_tool_object_null,
            self.ltla_one_a_missing_accommodation_export_tool_object_blank,
            self.ltla_one_a_missing_sponsor_tool_object_null,
            self.ltla_one_a_missing_sponsor_tool_object_blank,
            self.ltla_one_a_missing_rematched_host_tool_object_null,
            self.ltla_one_a_missing_rematched_host_tool_object_blank,
            self.utla_one_export_tool_object,
            self.sponsor_with_no_accommodation_export_tool_object,
            self.accommodation_with_no_la_sponsor_case_export_tool_object,
            self.accommodation_with_no_la_rematched_host_case_export_tool_object,
            self.accommodation_with_no_la_export_tool_object,
        ]

        self.user_with_da_other_export_tool_objects = [
            self.other_da_export_tool_object,
        ]

        self.da_england_export_tool_objects = [
            self.da_england_export_tool_object,
        ]

    def test_grants_no_access_if_no_groups(self):
        self.assert_get_for_user_returns(get_user_with_no_access(), [])

    def test_grants_correct_access_to_ltla_users(self):
        self.assert_get_for_user_returns(
            self.ltla_one_a_user,
            self.user_with_ltla_one_a_export_tool_objects,
        )

        self.assert_get_for_user_returns(
            self.ltla_one_b_user,
            self.user_with_ltla_one_b_export_tool_objects,
        )

        self.assert_get_for_user_returns(
            self.ltla_two_a_user,
            self.user_with_ltla_two_a_export_tool_objects,
        )

    def test_grants_access_to_multi_la_objects_if_you_have_the_accomm_request_groups(
        self,
    ):
        self.assert_get_for_user_returns(
            self.ltla_one_a_ltla_one_b_user,
            self.user_with_ltla_one_a_ltla_one_b_export_tool_objects,
        )

        self.assert_get_for_user_returns(
            get_user_with_groups(
                [self.ltla_one_a_group, self.ltla_one_b_group, self.ltla_two_a_group]
            ),
            self.user_with_ltla_one_a_ltla_one_b_ltla_two_a_export_tool_objects,
        )

    def test_grants_correct_access_to_utla_users(self):
        self.assert_get_for_user_returns(
            self.utla_one_user,
            self.user_with_utla_one_export_tool_objects,
        )

        self.assert_get_for_user_returns(
            self.utla_two_user,
            self.user_with_utla_two_export_tool_objects,
        )

    def test_grants_correct_access_to_da_users(self):
        self.assert_get_for_user_returns(
            self.da_main_user,
            self.user_with_da_main_export_tool_objects,
        )

        self.assert_get_for_user_returns(
            self.da_other_user,
            self.user_with_da_other_export_tool_objects,
        )

    def test_grants_correct_access_to_da_viewer_group(self):
        self.assert_get_for_user_returns(
            self.da_england_user,
            self.da_england_export_tool_objects,
        )
