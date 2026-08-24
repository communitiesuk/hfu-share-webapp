from django.db.models import QuerySet
from django.test import TestCase

from accounts.enums import BROWSER_TEST_LTLA_NAMES, GroupType
from accounts.models import User
from accounts.tests.factories import GroupFactory, UserFactory
from ontology.models import (
    MvPerson,
    SafeguardingReferral,
    VisaApplication,
    VisaInformationRequest,
)
from ontology.tests.base import LocalAuthorityPermissionsManagerBaseTestCase
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    SafeguardingReferralFactory,
    VIRFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class BrowserTestLaScopingTestCase(LocalAuthorityPermissionsManagerBaseTestCase):
    def setUp(self):
        super().setUp()

        self.browser_test_group = GroupFactory(
            name="ltla_hobbiton_browser_test",
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
        )
        self.browser_test_user = UserFactory()
        self.browser_test_user.groups.set([self.browser_test_group])

        self.browser_test_object = VisaApplicationFactory(
            ltla_name=BROWSER_TEST_LTLA_NAMES[0], utla_name=""
        )

    def assert_get_for_user_returns(
        self, user: User, visa_applications: list[VisaApplication]
    ):
        queryset: QuerySet[VisaApplication] = VisaApplication.objects.get_for_user(user)
        return self.assertQuerySetEqual(
            queryset.order_by("visa_application_id"),
            sorted(list({str(obj) for obj in visa_applications})),
            transform=str,
        )

    def test_dev_user_does_not_see_browser_test_records(self):
        self.assert_get_for_user_returns(self.ltla_user_dev, self.all_objects)

    def test_ukvi_user_does_not_see_browser_test_records(self):
        self.assert_get_for_user_returns(get_ukvi_user(), self.all_objects)

    def test_mhclg_user_does_not_see_browser_test_records(self):
        self.assert_get_for_user_returns(get_mhclg_user(), self.all_objects)

    def test_service_support_user_does_not_see_browser_test_records(self):
        self.assert_get_for_user_returns(get_service_support_user(), self.all_objects)

    def test_la_user_does_not_see_browser_test_records(self):
        self.assert_get_for_user_returns(self.ltla_one_a_user, self.ltla_one_a_objects)

    def test_da_user_does_not_see_browser_test_records(self):
        self.assert_get_for_user_returns(self.da_england_user, self.da_england_objects)

    def test_browser_test_user_sees_only_browser_test_records(self):
        self.assert_get_for_user_returns(
            self.browser_test_user, [self.browser_test_object]
        )


class BrowserTestLaGuardsTestCase(TestCase):
    def setUp(self):
        GroupFactory(
            name="ltla_hobbiton_browser_test",
            groupinfo__ltla_name=BROWSER_TEST_LTLA_NAMES[0],
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY_BROWSER_TEST,
        )
        self.browser_test_ar = MvAccommodationRequestFactory(
            ltla_name=[BROWSER_TEST_LTLA_NAMES[0]]
        )
        self.browser_test_person = MvPersonFactory(
            accommodation_request=self.browser_test_ar
        )
        self.real_ar = MvAccommodationRequestFactory(ltla_name=["Realshire"])
        self.real_person = MvPersonFactory(accommodation_request=self.real_ar)

        self.browser_test_referral = SafeguardingReferralFactory(
            person=self.browser_test_person
        )
        self.real_referral = SafeguardingReferralFactory(person=self.real_person)

        self.browser_test_vir = VIRFactory(
            visa_application=VisaApplicationFactory(
                ltla_name=BROWSER_TEST_LTLA_NAMES[0]
            )
        )
        self.real_vir = VIRFactory(
            visa_application=VisaApplicationFactory(ltla_name="Realshire")
        )

    def test_referrals_hidden_from_see_all_users(self):
        for user in [get_admin_user(), get_ukvi_user(), get_mhclg_user()]:
            referrals = SafeguardingReferral.objects.get_for_user(user)
            self.assertIn(self.real_referral, referrals)
            self.assertNotIn(self.browser_test_referral, referrals)

    def test_virs_hidden_from_see_all_users(self):
        for user in [get_admin_user(), get_ukvi_user(), get_mhclg_user()]:
            virs = VisaInformationRequest.objects.get_for_user(user)
            self.assertIn(self.real_vir, virs)
            self.assertNotIn(self.browser_test_vir, virs)

    def test_exclude_browser_test_records_on_plain_queryset(self):
        people = MvPerson.objects.exclude_browser_test_records(MvPerson.objects.all())
        self.assertIn(self.real_person, people)
        self.assertNotIn(self.browser_test_person, people)

    def test_see_all_users_cannot_load_browser_test_person(self):
        for user in [get_admin_user(), get_ukvi_user(), get_mhclg_user()]:
            people = MvPerson.objects.get_for_user(user)
            self.assertIn(self.real_person, people)
            self.assertNotIn(self.browser_test_person, people)
