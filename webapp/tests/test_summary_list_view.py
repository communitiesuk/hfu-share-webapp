from django.test import TestCase
from django.utils import timezone
from django_tables2 import Column

from accounts.models import User
from accounts.models.GroupProxy import GroupProxy
from accounts.tests.factories import GroupFactory, UserFactory
from ontology.models import (
    MvAccommodation,
    MvAccommodationRequest,
    MvPerson,
    MvVolunteer,
    ReassignmentRequest,
    SafeguardingReferral,
    VisaApplication,
)
from ontology.tests.factories import (
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvUkPostcodeFactory,
    MvVolunteerFactory,
    ReassignmentRequestFactory,
    SafeguardingReferralFactory,
    VisaApplicationFactory,
)
from webapp.views import SummaryListView, TwoColumnSummaryListView


def get_group_summary_list_view_with_user_set():
    test_user = UserFactory()
    test_group = GroupFactory(name="test group")
    test_user.groups.set([test_group])

    class GroupSummaryListView(SummaryListView):
        # pylint: disable=view-missing-access-control
        template = "group.html"
        model = GroupProxy
        object = test_group

        class Meta:
            fields = ["user_set"]

    return test_user, GroupSummaryListView()


def get_group_summary_list_view_with_linked_object():
    test_user = UserFactory()
    test_group = GroupFactory(
        name="test group", groupinfo__description="my description"
    )
    test_user.groups.set([test_group])

    class GroupSummaryListView(SummaryListView):
        # pylint: disable=view-missing-access-control
        template = "group.html"
        model = GroupProxy
        object = test_group

        class Meta:
            fields = ["groupinfo__description"]

    return GroupSummaryListView()


def get_user_summary_list_view_with_linked_objects():
    test_user = UserFactory()
    test_group = GroupFactory(
        name="test group", groupinfo__description="my description"
    )
    test_user.groups.set([test_group])

    class UserListSummaryView(SummaryListView):
        # pylint: disable=view-missing-access-control
        template = "user.html"
        model = User
        object = test_user

        class Meta:
            fields = ["logentry_set", "groups"]

    return test_user, UserListSummaryView()


def get_user_summary_list_view_default():
    test_user = UserFactory()
    test_group = GroupFactory(
        name="test group", groupinfo__description="my description"
    )
    test_user.groups.set([test_group])

    class UserListSummaryView(SummaryListView):
        # pylint: disable=view-missing-access-control
        template = "user.html"
        model = User
        object = test_user

    return test_user, UserListSummaryView()


class MvAccommodationRequestSummaryListViewWithMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvAccommodationRequest

    active_host = Column(verbose_name="Host")

    def render_active_host(self):
        return self.object.active_host.get_full_name()

    class Meta:
        fields = ["title", "checks_status", "active_host"]


class MvAccommodationRequestSummaryListViewWithoutMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvAccommodationRequest


class MvAccommodationRequestTwoColumnSummaryListView(TwoColumnSummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvAccommodationRequest

    class Meta:
        left_fields = ["title", "checks_status"]
        right_fields = ["number_of_people", "latest_application_date"]


class MvAccommodationSummaryListViewWithMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvAccommodation

    class Meta:
        fields = ["full_address", "postcode", "is_principal"]


class MvAccommodationSummaryListViewWithoutMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvAccommodation


class MvAccommodationTwoColumnSummaryListView(TwoColumnSummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvAccommodation

    class Meta:
        left_fields = ["full_address", "postcode"]
        right_fields = ["ltla_name", "utla_name"]


class MvVolunteerSummaryListViewWithMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvVolunteer

    class Meta:
        fields = ["first_name", "last_name", "email"]


class MvVolunteerSummaryListViewWithoutMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvVolunteer


class MvVolunteerTwoColumnSummaryListView(TwoColumnSummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvVolunteer

    class Meta:
        left_fields = ["first_name", "last_name"]
        right_fields = ["email", "phone_number"]


class MvPersonSummaryListViewWithMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvPerson

    class Meta:
        fields = ["first_name", "last_name"]


class MvPersonSummaryListViewWithoutMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvPerson


class MvPersonTwoColumnSummaryListView(TwoColumnSummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = MvPerson

    class Meta:
        left_fields = ["first_name"]
        right_fields = ["last_name"]


class SafeguardingReferralSummaryListViewWithMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = SafeguardingReferral

    class Meta:
        fields = ["id"]


class SafeguardingReferralSummaryListViewWithoutMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = SafeguardingReferral


class SafeguardingReferralTwoColumnSummaryListView(TwoColumnSummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = SafeguardingReferral

    person_has_new_uans = Column(verbose_name="Has new UANs")

    def render_person_has_new_uans(self):
        return "Yes" if self.object.person_has_new_uans else "No"

    class Meta:
        split_columns_at_field = "id"


class VisaApplicationSummaryListViewWithMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = VisaApplication

    class Meta:
        fields = ["title", "visa_status"]


class VisaApplicationSummaryListViewWithoutMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = VisaApplication


class VisaApplicationTwoColumnSummaryListView(TwoColumnSummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = VisaApplication

    class Meta:
        left_fields = ["title"]
        right_fields = ["visa_status"]


class ReassignmentRequestSummaryListViewWithMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = ReassignmentRequest

    class Meta:
        fields = ["id"]


class ReassignmentRequestSummaryListViewWithoutMeta(SummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = ReassignmentRequest


class ReassignmentRequestTwoColumnSummaryListView(TwoColumnSummaryListView):  # pylint: disable=view-missing-access-control
    template = "test.html"
    model = ReassignmentRequest

    accommodation_request_title = Column(verbose_name="Title")

    class Meta:
        left_fields = ["accommodation_request_title"]
        right_fields = ["comments"]


class OntologyModelSummaryListViewTestCase(TestCase):
    def setUp(self):
        host = MvVolunteerFactory(
            first_name="John",
            last_name="Doe",
            is_principal=True,
        )

        self.accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
            checks_status=MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
            latest_application_date=timezone.now(),
            active_host=host,
            ltla_name=["Kent"],
            utla_name=["Kent"],
        )

        self.accommodation = MvAccommodationFactory(
            full_address="123 Test Street, London",
            postcode=MvUkPostcodeFactory(postcode="NW5 1TL"),
            ltla_name="Bridgend",
            utla_name="Bridgend",
            is_principal=True,
        )

        self.volunteer = MvVolunteerFactory(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_number=["01134960698"],
            sex="Male",
            is_principal=True,
        )

        self.person = MvPersonFactory(
            first_name="Jane",
            last_name="Smith",
        )

        self.safeguarding_referral = SafeguardingReferralFactory(
            person=MvPersonFactory(),
            alerted_status=SafeguardingReferral.AlertedStatus.ALERTED,
            created_at=timezone.now(),
            comments="Test comments",
            person_has_new_uans=True,
        )

        self.visa_application = VisaApplicationFactory(
            title="Visa Application sponsored by Test Sponsor to Test Location",
            visa_status="Arrived",
            application_event_datetime=timezone.now(),
            visa_decision_date=timezone.now(),
            Q97c_sponsor_name="Test Sponsor Name",
            ltla_name="Cornwall",
            gwf="Test GWF 123456",
            application_unique_application_number="0000-1111-2222-3333",
        )

        self.reassignment_request = ReassignmentRequestFactory(
            source_ltla_name=["Southampton"],
            source_utla_name=["Hampshire"],
            destination_ltla_name="Cornwall",
            destination_utla_name="Cornwall",
            outcome=ReassignmentRequest.Outcome.PENDING,
            reason="Test reassignment reason",
        )

    # MvAccommodationRequest Tests
    def test_accommodation_request_summary_list_view_with_meta(self):
        view = MvAccommodationRequestSummaryListViewWithMeta()
        view.object = self.accommodation_request
        context = view.get_context_data()

        self.assertEqual(
            [
                ("Title", self.accommodation_request.title),
                ("Checks status", self.accommodation_request.checks_status.label),
                ("Host", self.accommodation_request.active_host.get_full_name()),
            ],
            context["fields"],
        )

    def test_accommodation_request_summary_list_view_without_meta(self):
        view = MvAccommodationRequestSummaryListViewWithoutMeta()
        view.object = self.accommodation_request
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        field_dict = {label: value for label, value in context["fields"]}
        self.assertIn("Title", field_dict)
        self.assertEqual(field_dict["Title"], self.accommodation_request.title)

    def test_accommodation_request_two_column_summary_list_view(self):
        view = MvAccommodationRequestTwoColumnSummaryListView()
        view.object = self.accommodation_request
        context = view.get_context_data()

        self.assertIn("left_fields", context)
        self.assertIn("right_fields", context)
        self.assertTrue(len(context["left_fields"]) > 0)
        self.assertTrue(len(context["right_fields"]) > 0)

        left_dict = {label: value for label, value in context["left_fields"]}
        right_dict = {label: value for label, value in context["right_fields"]}
        self.assertEqual(left_dict.get("Title"), self.accommodation_request.title)
        self.assertEqual(
            left_dict.get("Checks status"),
            self.accommodation_request.checks_status.label,
        )
        self.assertEqual(
            right_dict.get("Number of people"),
            self.accommodation_request.number_of_people,
        )
        self.assertEqual(
            right_dict.get("Latest application date"),
            self.accommodation_request.latest_application_date,
        )

    # MvAccommodation Tests
    def test_accommodation_summary_list_view_with_meta(self):
        view = MvAccommodationSummaryListViewWithMeta()
        view.object = self.accommodation
        context = view.get_context_data()

        self.assertEqual(
            [
                ("Address", self.accommodation.full_address),
                ("Postcode", str(self.accommodation.postcode.id)),
                ("Is principal", self.accommodation.is_principal),
            ],
            context["fields"],
        )

    def test_accommodation_summary_list_view_without_meta(self):
        view = MvAccommodationSummaryListViewWithoutMeta()
        view.object = self.accommodation
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        field_dict = {label: value for label, value in context["fields"]}
        self.assertIn("Address", field_dict)
        self.assertEqual(field_dict["Address"], self.accommodation.full_address)

    def test_accommodation_two_column_summary_list_view(self):
        view = MvAccommodationTwoColumnSummaryListView()
        view.object = self.accommodation
        context = view.get_context_data()

        self.assertIn("left_fields", context)
        self.assertIn("right_fields", context)
        self.assertTrue(len(context["left_fields"]) > 0)
        self.assertTrue(len(context["right_fields"]) > 0)

        left_dict = {label: value for label, value in context["left_fields"]}
        right_dict = {label: value for label, value in context["right_fields"]}
        self.assertEqual(left_dict.get("Address"), self.accommodation.full_address)
        self.assertEqual(right_dict.get("Lower tier LA"), self.accommodation.ltla_name)
        self.assertEqual(right_dict.get("Upper tier LA"), self.accommodation.utla_name)

    # MvVolunteer Tests
    def test_volunteer_summary_list_view_with_meta(self):
        view = MvVolunteerSummaryListViewWithMeta()
        view.object = self.volunteer
        context = view.get_context_data()

        self.assertEqual(
            [
                ("First name", self.volunteer.first_name),
                ("Last name", self.volunteer.last_name),
                ("Email", self.volunteer.email),
            ],
            context["fields"],
        )

    def test_volunteer_summary_list_view_without_meta(self):
        view = MvVolunteerSummaryListViewWithoutMeta()
        view.object = self.volunteer
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        field_dict = {label: value for label, value in context["fields"]}
        self.assertIn("First name", field_dict)
        self.assertEqual(field_dict["First name"], self.volunteer.first_name)

    def test_volunteer_two_column_summary_list_view(self):
        view = MvVolunteerTwoColumnSummaryListView()
        view.object = self.volunteer
        context = view.get_context_data()

        self.assertIn("left_fields", context)
        self.assertIn("right_fields", context)
        self.assertTrue(len(context["left_fields"]) > 0)
        self.assertTrue(len(context["right_fields"]) > 0)

        left_dict = {label: value for label, value in context["left_fields"]}
        right_dict = {label: value for label, value in context["right_fields"]}
        self.assertEqual(left_dict.get("First name"), self.volunteer.first_name)
        self.assertEqual(left_dict.get("Last name"), self.volunteer.last_name)
        self.assertEqual(right_dict.get("Email"), self.volunteer.email)

    # MvPerson Tests
    def test_person_summary_list_view_with_meta(self):
        view = MvPersonSummaryListViewWithMeta()
        view.object = self.person
        context = view.get_context_data()

        self.assertEqual(
            [
                ("First name", self.person.first_name),
                ("Last name", self.person.last_name),
            ],
            context["fields"],
        )

    def test_person_summary_list_view_without_meta(self):
        view = MvPersonSummaryListViewWithoutMeta()
        view.object = self.person
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        field_dict = {label: value for label, value in context["fields"]}
        self.assertIn("First name", field_dict)
        self.assertEqual(field_dict["First name"], self.person.first_name)

    def test_person_two_column_summary_list_view(self):
        view = MvPersonTwoColumnSummaryListView()
        view.object = self.person
        context = view.get_context_data()

        self.assertIn("left_fields", context)
        self.assertIn("right_fields", context)
        self.assertTrue(len(context["left_fields"]) > 0)
        self.assertTrue(len(context["right_fields"]) > 0)

        left_dict = {label: value for label, value in context["left_fields"]}
        right_dict = {label: value for label, value in context["right_fields"]}
        self.assertEqual(left_dict.get("First name"), self.person.first_name)
        self.assertEqual(right_dict.get("Last name"), self.person.last_name)

    # SafeguardingReferral Tests
    def test_safeguarding_referral_summary_list_view_with_meta(self):
        view = SafeguardingReferralSummaryListViewWithMeta()
        view.object = self.safeguarding_referral
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        field_dict = {label: value for label, value in context["fields"]}
        self.assertIn("Id", field_dict)
        self.assertEqual(field_dict["Id"], self.safeguarding_referral.id)

    def test_safeguarding_referral_summary_list_view_without_meta(self):
        view = SafeguardingReferralSummaryListViewWithoutMeta()
        view.object = self.safeguarding_referral
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        self.assertEqual(
            self.safeguarding_referral.alerted_status,
            SafeguardingReferral.AlertedStatus.ALERTED,
        )

    def test_safeguarding_referral_two_column_summary_list_view(self):
        view = SafeguardingReferralTwoColumnSummaryListView()
        view.object = self.safeguarding_referral
        context = view.get_context_data()

        self.assertIn("left_fields", context)
        self.assertIn("right_fields", context)
        self.assertTrue(len(context["left_fields"]) > 0)
        self.assertTrue(len(context["right_fields"]) > 0)

        right_dict = {label: value for label, value in context["right_fields"]}
        left_dict = {label: value for label, value in context["left_fields"]}

        self.assertEqual(
            left_dict.get("Alerted status"),
            self.safeguarding_referral.alerted_status.label,
        )
        self.assertEqual(left_dict.get("Comments"), self.safeguarding_referral.comments)
        self.assertEqual(
            right_dict.get("Has new UANs"),
            "Yes",
        )

    # VisaApplication Tests
    def test_visa_application_summary_list_view_with_meta(self):
        view = VisaApplicationSummaryListViewWithMeta()
        view.object = self.visa_application
        context = view.get_context_data()

        self.assertEqual(
            [
                ("Title", self.visa_application.title),
                ("Visa status", self.visa_application.visa_status),
            ],
            context["fields"],
        )

    def test_visa_application_summary_list_view_without_meta(self):
        view = VisaApplicationSummaryListViewWithoutMeta()
        view.object = self.visa_application
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        field_dict = {label: value for label, value in context["fields"]}
        self.assertIn("Title", field_dict)
        self.assertEqual(field_dict["Title"], self.visa_application.title)

    def test_visa_application_two_column_summary_list_view(self):
        view = VisaApplicationTwoColumnSummaryListView()
        view.object = self.visa_application
        context = view.get_context_data()

        self.assertIn("left_fields", context)
        self.assertIn("right_fields", context)
        self.assertTrue(len(context["left_fields"]) > 0)
        self.assertTrue(len(context["right_fields"]) > 0)

        left_dict = {label: value for label, value in context["left_fields"]}
        right_dict = {label: value for label, value in context["right_fields"]}
        self.assertEqual(left_dict.get("Title"), self.visa_application.title)
        self.assertEqual(
            right_dict.get("Visa status"), self.visa_application.visa_status
        )

    # ReassignmentRequest Tests
    def test_reassignment_request_summary_list_view_with_meta(self):
        view = ReassignmentRequestSummaryListViewWithMeta()
        view.object = self.reassignment_request
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)
        field_dict = {label: value for label, value in context["fields"]}
        self.assertIn("Id", field_dict)
        self.assertEqual(field_dict["Id"], self.reassignment_request.id)

    def test_reassignment_request_summary_list_view_without_meta(self):
        view = ReassignmentRequestSummaryListViewWithoutMeta()
        view.object = self.reassignment_request
        context = view.get_context_data()

        self.assertIn("fields", context)
        self.assertTrue(len(context["fields"]) > 0)

        self.assertEqual(
            self.reassignment_request.outcome, ReassignmentRequest.Outcome.PENDING
        )
        self.assertEqual(self.reassignment_request.reason, "Test reassignment reason")

    def test_reassignment_request_two_column_summary_list_view(self):
        view = ReassignmentRequestTwoColumnSummaryListView()
        view.object = self.reassignment_request
        context = view.get_context_data()

        self.assertIn("left_fields", context)
        self.assertIn("right_fields", context)
        self.assertTrue(len(context["left_fields"]) > 0)
        self.assertTrue(len(context["right_fields"]) > 0)

        left_dict = {label: value for label, value in context["left_fields"]}
        right_dict = {label: value for label, value in context["right_fields"]}
        self.assertEqual(
            left_dict.get("Title"),
            self.reassignment_request.accommodation_request_title,
        )
        self.assertEqual(
            right_dict.get("Comments"),
            self.reassignment_request.comments,
        )
