from django.http import Http404
from django.test import RequestFactory
from django.views.generic import DetailView, ListView

from accounts.models import User
from ontology.models import VisaApplication
from ontology.tests.base import VisaApplicationBaseTestCase
from webapp.mixins import LocalAuthorityAccessMixin


class TestLocalAuthorityAccessMixinListView(LocalAuthorityAccessMixin, ListView):
    # pylint: disable=view-missing-access-control
    model = VisaApplication


class TestLocalAuthorityAccessMixinDetailView(LocalAuthorityAccessMixin, DetailView):
    # pylint: disable=view-missing-access-control
    model = VisaApplication


class LocalAuthorityAccessMixinTestCase(VisaApplicationBaseTestCase):
    # Using Visa Applications as a proxy model to test this
    # Minimal as covered by LocalAuthorityPermissionsManager tests

    def assert_get_queryset_returns(
        self, user: User, visa_applications: list[VisaApplication]
    ):
        list_view = TestLocalAuthorityAccessMixinListView()
        list_view.request = RequestFactory().get("/")
        list_view.request.user = user
        return self.assertQuerySetEqual(
            list_view.get_queryset().order_by("visa_application_id"),
            sorted(list({str(obj) for obj in visa_applications})),
            transform=str,
        )

    def _get_object_wrapper(self, user: User, application: VisaApplication):
        detail_view = TestLocalAuthorityAccessMixinDetailView()
        detail_view.request = RequestFactory().get("/")
        detail_view.request.user = user
        detail_view.kwargs = {"pk": application.pk}
        return detail_view.get_object()

    def assert_get_object_returns(self, user: User, application: VisaApplication):
        return self.assertEqual(
            self._get_object_wrapper(user, application).pk,
            str(application.pk),
        )

    def assert_get_object_does_not_return(
        self, user: User, application: VisaApplication
    ):
        with self.assertRaises(Http404):
            self._get_object_wrapper(user, application)

    def test_get_queryset_returns_all_visa_applications_for_dev_user(self):
        self.assert_get_queryset_returns(
            self.ltla_user_dev,
            self.all_visa_applications,
        )

    def test_get_queryset_returns_only_visa_applications_matching_groups_single_la(
        self,
    ):
        self.assert_get_queryset_returns(
            self.ltla_one_a_user, [self.ltla_one_a_visa_application]
        )

        self.assert_get_queryset_returns(
            self.ltla_two_a_user, [self.ltla_two_a_visa_application]
        )

    def test_get_queryset_returns_only_visa_applications_matching_groups_multi_la(
        self,
    ):
        self.ltla_one_a_user.groups.set([self.ltla_one_a_group, self.ltla_two_a_group])

        self.assert_get_queryset_returns(
            self.ltla_one_a_user,
            [self.ltla_one_a_visa_application, self.ltla_two_a_visa_application],
        )

    def test_get_queryset_returns_only_visa_applications_matching_groups_single_utla(
        self,
    ):
        self.assert_get_queryset_returns(
            self.utla_one_user, [self.ltla_one_a_visa_application]
        )

        self.assert_get_queryset_returns(
            self.utla_two_user, [self.ltla_two_a_visa_application]
        )

    def test_get_queryset_returns_only_visa_applications_matching_groups_multi_utla(
        self,
    ):
        self.assert_get_queryset_returns(
            self.multi_utla_user,
            [self.ltla_one_a_visa_application, self.ltla_two_a_visa_application],
        )

    def test_get_object_returns_all_visa_applications_for_dev_user(self):
        self.assert_get_object_returns(
            self.ltla_user_dev,
            self.ltla_one_a_visa_application,
        )

        self.assert_get_object_returns(
            self.ltla_user_dev,
            self.ltla_two_a_visa_application,
        )

    def test_get_object_returns_only_visa_applications_matching_groups_single_la(
        self,
    ):
        self.assert_get_object_returns(
            self.ltla_one_a_user, self.ltla_one_a_visa_application
        )

        self.assert_get_object_does_not_return(
            self.ltla_one_a_user, self.ltla_two_a_visa_application
        )

    def test_get_object_returns_only_visa_applications_matching_groups_multi_la(
        self,
    ):
        self.ltla_one_a_user.groups.set([self.ltla_one_a_group, self.ltla_two_a_group])

        self.assert_get_object_returns(
            self.ltla_one_a_user,
            self.ltla_one_a_visa_application,
        )

        self.assert_get_object_returns(
            self.ltla_one_a_user,
            self.ltla_two_a_visa_application,
        )

    def test_get_object_returns_only_visa_applications_matching_groups_single_utla(
        self,
    ):
        self.assert_get_object_returns(
            self.utla_one_user, self.ltla_one_a_visa_application
        )

        self.assert_get_object_does_not_return(
            self.utla_one_user, self.ltla_two_a_visa_application
        )

        self.assert_get_object_returns(
            self.utla_two_user, self.ltla_two_a_visa_application
        )

        self.assert_get_object_does_not_return(
            self.utla_two_user, self.ltla_one_a_visa_application
        )

    def test_get_object_returns_only_visa_applications_matching_groups_multi_utla(
        self,
    ):
        self.assert_get_object_returns(
            self.multi_utla_user,
            self.ltla_one_a_visa_application,
        )

        self.assert_get_object_returns(
            self.multi_utla_user,
            self.ltla_two_a_visa_application,
        )
