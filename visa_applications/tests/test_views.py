from datetime import datetime, timezone
from unittest.mock import patch

from django.db.models import QuerySet
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse
from freezegun import freeze_time

from accounts.tests.base import TestSessionTokenMixin
from ontology.models import (
    MvPerson,
    MvVolunteer,
    VisaApplication,
    VisaInformationRequest,
    VisaInformationRequestComments,
)
from ontology.tests.base import (
    LocalAuthorityBaseTestCaseMixin,
    VisaApplicationBaseTestCase,
)
from ontology.tests.factories import (
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_ukvi_user,
)
from visa_applications.forms import AddVIRCommentForm, StartVIRForm
from visa_applications.views import (
    VisaApplicationLinkedRecordsView,
    VisaApplicationListView,
    VisaApplicationOverviewView,
    VisaApplicationPropertiesView,
    VisaApplicationVIRView,
)


class LocalAuthorityFilteredViews(VisaApplicationBaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get("/")
        self.request.user = self.ltla_one_a_user

    def assert_query_set_equal_to_list(
        self, qs: QuerySet, volunteers: list[MvVolunteer]
    ):
        return self.assertQuerySetEqual(
            qs.order_by("pk"),
            sorted(volunteers, key=lambda a: a.pk),
        )

    def test_get_queryset_for_user(self):
        """
        Test that get_queryset returns for the regular user.
        """

        view = VisaApplicationListView()
        view.request = self.request

        self.assert_query_set_equal_to_list(
            view.get_queryset(),
            [self.ltla_one_a_visa_application],
        )

    def test_get_queryset_returns_all_for_dev_user(self):
        """
        Test that get_queryset returns all objects for a dev user.
        """

        self.request.user = self.ltla_user_dev
        view = VisaApplicationListView()
        view.request = self.request

        self.assert_query_set_equal_to_list(
            view.get_queryset(),
            self.all_visa_applications,
        )

    def test_get_queryset_returns_objects_matching_search(self):
        """
        Test that get_queryset returns all objects matching a search.
        """
        self.request = RequestFactory().get("/", {"search": "test_ltla_one"})
        self.request.user = self.ltla_user_dev

        view_func = VisaApplicationListView.as_view()
        response = view_func(self.request)
        context = response.context_data

        self.assertQuerySetEqual(
            context["object_list"],
            [self.ltla_one_a_visa_application],
        )

    def test_get_object_calls_super_for_regular_user(self):
        """
        Test that get_object returns correctly for the user.
        """

        view = VisaApplicationPropertiesView()
        view.request = self.request
        view.kwargs = {"pk": self.ltla_one_a_visa_application.pk}

        obj = view.get_object()
        self.assertEqual(obj.pk, str(self.ltla_one_a_visa_application.pk))

    def test_get_object_denies_access_if_user_is_not_allowed(self):
        """
        Test that get_object raises Http404.
        """

        view = VisaApplicationPropertiesView()
        view.request = self.request
        view.kwargs = {"pk": self.ltla_two_a_visa_application.pk}

        with self.assertRaises(Http404):
            view.get_object()


class TestVisaApplicationDetailView(VisaApplicationPropertiesView):
    """
    VisaApplicationDetailView with overridden field list for testing.
    """

    class Meta:
        fields = [
            "gwf",
            "mapping_postcode",
            "Q101a_uk_address_staying",
            "Q2a_living_ukraine_before_jan_22",
            "Q31a_other_people_will_live_at_address",
            "Q3a_sponsor_uk_permission",
            "Q3b_sponsor_description",
            "visa_decision_date",
        ]
        split_properties_columns_at_field = "mapping_postcode"


class VisaApplicationDetailsTwoColumnViewTest(
    TestSessionTokenMixin, LocalAuthorityBaseTestCaseMixin, TestCase
):
    def test_fields_split_and_sorted_correctly(self):
        """
        Test that fields are split and sorted correctly.
        """
        view = TestVisaApplicationDetailView()
        view.object = VisaApplication()
        factory = RequestFactory()
        request = factory.get("/")
        request.user = get_admin_user()
        view.request = request
        context = view.get_context_data()

        properties_left_field_names = [field[0] for field in context["properties_left"]]
        properties_right_field_names = [
            field[0] for field in context["properties_right"]
        ]
        questions_left_field_names = [field[0] for field in context["questions_left"]]
        questions_right_field_names = [field[0] for field in context["questions_right"]]

        expected_property_field_names = [
            "GWF",
            "Mapping postcode",
            "Visa decision date",
        ]
        expected_question_field_names = [  # Sorted by number, not just alphanumeric
            "Q2a living Ukraine before Jan 22",
            "Q3a sponsor UK permission",
            "Q3b sponsor description",
            "Q31a other people will live at address",
            "Q101a UK address staying",
        ]

        self.assertEqual(properties_left_field_names, expected_property_field_names[:1])
        self.assertEqual(
            properties_right_field_names, expected_property_field_names[1:]
        )
        self.assertEqual(questions_left_field_names, expected_question_field_names[:3])
        self.assertEqual(questions_right_field_names, expected_question_field_names[3:])

    def test_fields_are_rendered(self):
        self.visa_app = VisaApplicationFactory(
            application_unique_application_number="UAN123",
            gwf="GWF1234567",
            mapping_postcode="AB1 3ER",
            visa_decision_date=datetime(2025, 3, 25, 9, 15, tzinfo=timezone.utc),
            Q101a_uk_address_staying="123 Test Street, Test City",
            Q3b_sponsor_description="Test Sponsor",
        )
        user = get_admin_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "visa-applications:detail-properties",
                args=[self.visa_app.pk],
            )
        )

        self.assertContains(response, "GWF1234567")
        self.assertContains(response, "AB1 3ER")
        self.assertContains(response, "123 Test Street, Test City")
        self.assertContains(response, "Test Sponsor")


class VisaApplicationOverviewViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.application = VisaApplication.objects.create(
            visa_application_id="test123",
            Q44g_full_name="John Doe",
            application_event_datetime=datetime(
                2025, 3, 24, 14, 30, tzinfo=timezone.utc
            ),
            visa_decision_date=datetime(2025, 3, 25, 9, 15, tzinfo=timezone.utc),
            ltla_name="Test Authority",
            gwf="GWF1234567",
        )

    def test_visa_application_detail_overview_displays_correct_details(self):
        visa_application = VisaApplicationFactory(
            application_unique_application_number="123456",
            visa_status="Withdrawn",
            application_event_datetime=datetime(
                2025, 3, 24, 14, 30, tzinfo=timezone.utc
            ),
            visa_decision_date=datetime(2025, 3, 25, 9, 15, tzinfo=timezone.utc),
            ltla_name="LTLA",
            gwf="1234-5678=9012",
        )

        linked_guest = MvPersonFactory(
            application_number=[visa_application.application_unique_application_number]
        )
        linked_sponsor = MvVolunteerFactory(
            application_unique_application_number=[
                visa_application.application_unique_application_number
            ],
        )

        request = self.factory.get("/")
        request.user = get_admin_user()

        view = VisaApplicationOverviewView()
        view.request = request
        view.object = visa_application

        context = view.get_context_data()
        fields = dict(context["fields"])

        self.assertIn("Guest name", fields)
        self.assertIn(linked_guest.get_full_name(), fields["Guest name"])

        self.assertIn("Visa status", fields)
        self.assertIn(visa_application.visa_status, fields["Visa status"])

        self.assertIn("Application date", fields)
        self.assertIn("24 Mar 2025 at 2:30pm", fields["Application date"])

        self.assertIn("Decision date", fields)
        self.assertIn("25 Mar 2025 at 9:15am", fields["Decision date"])

        self.assertIn("Sponsor name", fields)
        self.assertIn(linked_sponsor.get_full_name(), fields["Sponsor name"])

        self.assertIn("Local authority", fields)
        self.assertIn(visa_application.ltla_name, fields["Local authority"])

        self.assertIn("Global web form number (GWF)", fields)
        self.assertIn(visa_application.gwf, fields["Global web form number (GWF)"])

        self.assertIn("Unique application number (UAN)", fields)
        self.assertIn(
            visa_application.application_unique_application_number,
            fields["Unique application number (UAN)"],
        )

    def test_visa_application_detail_overview_hides_details_outside_of_users_la(self):
        visa_application = VisaApplicationFactory(
            application_unique_application_number="123456",
            visa_status="Withdrawn",
            application_event_datetime=datetime(
                2025, 3, 24, 14, 30, tzinfo=timezone.utc
            ),
            visa_decision_date=datetime(2025, 3, 25, 9, 15, tzinfo=timezone.utc),
            ltla_name="LTLA",
            gwf="1234-5678-9012",
        )

        linked_guest = MvPersonFactory(
            application_number=[visa_application.application_unique_application_number]
        )
        linked_sponsor = MvVolunteerFactory(
            application_unique_application_number=[
                visa_application.application_unique_application_number
            ],
        )

        request = self.factory.get("/")
        request.user = get_la_user()

        view = VisaApplicationOverviewView()
        view.request = request
        view.object = visa_application

        context = view.get_context_data()
        fields = dict(context["fields"])

        self.assertIn("Guest name", fields)
        self.assertEqual([], fields["Guest name"])
        self.assertNotIn(linked_guest, fields["Guest name"])

        self.assertIn("Visa status", fields)
        self.assertIn(visa_application.visa_status, fields["Visa status"])

        self.assertIn("Application date", fields)
        self.assertIn("24 Mar 2025 at 2:30pm", fields["Application date"])

        self.assertIn("Decision date", fields)
        self.assertIn("25 Mar 2025 at 9:15am", fields["Decision date"])

        self.assertIn("Sponsor name", fields)
        self.assertEqual([], fields["Sponsor name"])
        self.assertNotIn(linked_sponsor.get_full_name(), fields["Sponsor name"])

        self.assertIn("Local authority", fields)
        self.assertIn(visa_application.ltla_name, fields["Local authority"])

        self.assertIn("Global web form number (GWF)", fields)
        self.assertIn(visa_application.gwf, fields["Global web form number (GWF)"])

        self.assertIn("Unique application number (UAN)", fields)
        self.assertIn(
            visa_application.application_unique_application_number,
            fields["Unique application number (UAN)"],
        )

    def test_overview_view_renders_dates_correctly(self):
        request = self.factory.get("/")
        request.user = get_la_user()
        view = VisaApplicationOverviewView()
        view.request = request
        view.object = self.application

        context = view.get_context_data()
        fields = dict(context["fields"])
        app_date = fields["Application date"]
        decision_date = fields["Decision date"]

        self.assertIn("Mar 2025 at", app_date)
        self.assertIn("Mar 2025 at", decision_date)
        self.assertTrue(app_date.endswith("am") or app_date.endswith("pm"))
        self.assertTrue(decision_date.endswith("am") or decision_date.endswith("pm"))

    def test_overview_view_handles_null_dates(self):
        visa_application = VisaApplicationFactory(
            application_unique_application_number="123456",
            visa_status="Withdrawn",
            application_event_datetime=None,
            visa_decision_date=None,
            ltla_name="LTLA",
            gwf="1234-5678-9012",
        )

        request = self.factory.get("/")
        request.user = get_la_user()
        view = VisaApplicationOverviewView()
        view.request = request
        view.object = visa_application

        context = view.get_context_data()
        fields = dict(context["fields"])

        self.assertIsNone(fields["Application date"])
        self.assertIsNone(fields["Decision date"])


class VisaApplicationLinkedRecordsViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.sponsor = MvVolunteerFactory(id="s1")
        self.accommodation_request = MvAccommodationRequestFactory(
            id="ar1",
            unique_application_number=["UAN1", "UAN2"],
            active_host=self.sponsor,
            ltla_name=["Test Authority"],
            utla_name=["Test Authority"],
        )
        self.guest = MvPersonFactory(
            id="g1",
            application_number=["UAN1", "UAN3"],
            accommodation_request=self.accommodation_request,
        )
        self.visa_application = VisaApplicationFactory(
            visa_application_id="va1", application_unique_application_number="UAN1"
        )

    def test_linked_records_context(self):
        request = self.factory.get("/visa-applications/va1/linked-records")
        request.user = get_admin_user()
        view = VisaApplicationLinkedRecordsView()
        view.request = request
        view.object = self.visa_application
        context = view.get_context_data()
        fields = dict(context["fields"])
        self.assertIn("Guest", fields)
        self.assertIn(self.guest, fields["Guest"])
        self.assertIn("Accommodation request", fields)
        self.assertIn(self.accommodation_request, fields["Accommodation request"])
        self.assertIn("Host", fields)
        self.assertIn(self.sponsor, fields["Host"])


class TestVirViews(TestSessionTokenMixin, TestCase):
    def test_access_virs_shows_results_if_da_user(self):
        user = get_da_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "visa-applications:visa-information-requests",
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_access_virs_shows_results_if_la_user(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "visa-applications:visa-information-requests",
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_access_virs_shows_results_if_ukvi_user(self):
        user = get_ukvi_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "visa-applications:visa-information-requests",
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)


class VisaApplicationVIRViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_ukvi_user()
        self.visa_application = VisaApplicationFactory(
            application_unique_application_number="UAN123456789",
            ltla_name="Test LTLA",
            utla_name="Test UTLA",
        )

        self.person = MvPerson.objects.create(
            id="person1",
            application_number=[
                self.visa_application.application_unique_application_number
            ],
        )
        self.request = self.factory.post(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk]),
            data={
                "request_type": VisaInformationRequest.RequestType.GENERAL.value,
                "requested_check_type_id": [
                    VisaInformationRequest.RequestedCheckType.ACCOMM_SUITABLE.value,
                    VisaInformationRequest.RequestedCheckType.SPONSOR_DBS.value,
                ],
                "comment": "Test comment for VIR",
            },
        )
        self.request.user = self.user

    @freeze_time("2025-07-29 12:00:00+00:00")
    def test_handle_start_vir_creates_vir_and_comment(self):
        form = StartVIRForm(
            data={
                "request_type": VisaInformationRequest.RequestType.GENERAL.value,
                "requested_check_type_id": [
                    VisaInformationRequest.RequestedCheckType.ACCOMM_SUITABLE.value,
                    VisaInformationRequest.RequestedCheckType.SPONSOR_DBS.value,
                ],
                "comment": "Test comment for VIR",
            }
        )
        self.assertTrue(form.is_valid())
        view = VisaApplicationVIRView()
        view.request = self.request
        view.object = self.visa_application

        # Patch messages.success so we don't need to set up messages storage
        with patch("django.contrib.messages.success"):
            response = view.handle_start_vir(form)

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk]),
            response.url,
        )

        vir = VisaInformationRequest.objects.latest("created_at")
        expected_dt = datetime(2025, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(vir.created_at, expected_dt)
        self.assertEqual(vir.created_by, self.user.username)
        self.assertEqual(vir.requested_at, expected_dt)
        self.assertEqual(vir.request_type, VisaInformationRequest.RequestType.GENERAL)
        self.assertEqual(
            vir.requested_check_type_id,
            [
                VisaInformationRequest.RequestedCheckType.ACCOMM_SUITABLE.value,
                VisaInformationRequest.RequestedCheckType.SPONSOR_DBS.value,
            ],
        )
        self.assertEqual(
            vir.request_status, VisaInformationRequest.RequestStatus.AWAITING_LA
        )
        self.assertEqual(
            vir.visa_application,
            self.visa_application,
        )
        self.assertEqual(vir.ltla_name, "Test LTLA")
        self.assertEqual(vir.utla_name, "Test UTLA")

        comments = VisaInformationRequestComments.objects.filter(
            visa_information_request=vir
        )
        comment = comments.first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.comment, "Test comment for VIR")
        self.assertEqual(comment.created_at, expected_dt)
        self.assertEqual(comment.created_by_uid, self.user.username)

    def test_handle_start_vir_with_one_requested_check_type_id(self):
        form = StartVIRForm(
            data={
                "request_type": (
                    VisaInformationRequest.RequestType.CHILD_SPONSORED_BY_PARENTS.value
                ),
                "requested_check_type_id": [
                    VisaInformationRequest.RequestedCheckType.ACCOMM_SUITABLE.value
                ],
                "comment": "Test comment for VIR with one check",
            }
        )
        view = VisaApplicationVIRView()
        view.request = self.request
        view.object = self.visa_application

        # Patch messages.success so we don't need to set up messages storage
        with patch("django.contrib.messages.success"):
            view.handle_start_vir(form)

        vir = VisaInformationRequest.objects.latest("created_at")
        self.assertEqual(
            vir.requested_check_type_id,
            [VisaInformationRequest.RequestedCheckType.ACCOMM_SUITABLE.value],
        )

        comments = VisaInformationRequestComments.objects.filter(
            visa_information_request=vir
        )
        comment = comments.first()
        self.assertIsNotNone(comment)


class VisaApplicationVIRViewAddCommentTests(TestCase):
    def setUp(self):
        fixed_datetime = datetime(2025, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
        self.factory = RequestFactory()
        self.visa_application = VisaApplicationFactory(
            application_unique_application_number="UAN123456789",
            ltla_name="Test LTLA",
            utla_name="Test UTLA",
        )
        self.person = MvPerson.objects.create(
            id="person1",
            application_number=[
                self.visa_application.application_unique_application_number
            ],
        )
        self.vir = VisaInformationRequest.objects.create(
            visa_information_request_id="vir1",
            visa_application=self.visa_application,
            request_type=VisaInformationRequest.RequestType.GENERAL,
            requested_check_type_id=[
                VisaInformationRequest.RequestedCheckType.ACCOMM_SUITABLE.value,
                VisaInformationRequest.RequestedCheckType.SPONSOR_DBS.value,
            ],
            request_status=VisaInformationRequest.RequestStatus.AWAITING_LA,
            created_by="ukviuser",
            created_at=fixed_datetime,
            requested_at=fixed_datetime,
            ltla_name="Test LTLA",
            utla_name="Test UTLA",
        )
        self.initial_comment = VisaInformationRequestComments.objects.create(
            id="comment1",
            visa_information_request=self.vir,
            comment="Initial comment",
            created_at=fixed_datetime,
            created_by_uid="ukviuser",
        )

    def _post_add_comment(self, user, comment_text):
        request = self.factory.post(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk]),
            data={
                "comment": comment_text,
                "add_comment_submit": "Add comment",
            },
        )
        request.user = user
        view = VisaApplicationVIRView()
        view.request = request
        view.object = self.visa_application
        form = AddVIRCommentForm(data={"comment": comment_text})
        with patch("django.contrib.messages.success"):
            response = view.handle_add_comment(form)
        return response

    def test_add_comment_display_name_ukvi(self):
        user = get_ukvi_user()
        comment_text = "UKVI user comment"
        self._post_add_comment(user, comment_text)
        view = VisaApplicationVIRView()
        view.request = self.factory.get("/")
        view.request.user = user
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        all_comments = [c for clist in context["conversations"].values() for c in clist]
        latest_comment = next(
            (c for c in all_comments if c.comment == comment_text), None
        )
        self.assertIsNotNone(latest_comment)
        self.assertEqual(latest_comment.display_name, "UKVI")

    def test_add_comment_display_name_la(self):
        user = get_la_user()
        comment_text = "LA user comment"
        self._post_add_comment(user, comment_text)
        view = VisaApplicationVIRView()
        view.request = self.factory.get("/")
        view.request.user = user
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        all_comments = [c for clist in context["conversations"].values() for c in clist]
        latest_comment = next(
            (c for c in all_comments if c.comment == comment_text), None
        )
        self.assertIsNotNone(latest_comment)
        self.assertIn(
            latest_comment.display_name,
            [user.groups.first().groupinfo.ltla_name, "Local Authority User"],
        )

    def test_add_comment_display_name_admin(self):
        user = get_admin_user()
        comment_text = "Admin user comment"
        self._post_add_comment(user, comment_text)
        view = VisaApplicationVIRView()
        view.request = self.factory.get("/")
        view.request.user = user
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        all_comments = [c for clist in context["conversations"].values() for c in clist]
        latest_comment = next(
            (c for c in all_comments if c.comment == comment_text), None
        )
        self.assertIsNotNone(latest_comment)
        self.assertEqual(latest_comment.display_name, "MHCLG Admin")

    def test_add_comment_display_name_mhclg_ops(self):
        user = get_mhclg_user()
        comment_text = "MHCLG Ops user comment"
        self._post_add_comment(user, comment_text)
        view = VisaApplicationVIRView()
        view.request = self.factory.get("/")
        view.request.user = user
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        all_comments = [c for clist in context["conversations"].values() for c in clist]
        latest_comment = next(
            (c for c in all_comments if c.comment == comment_text), None
        )
        self.assertIsNotNone(latest_comment)
        self.assertEqual(latest_comment.display_name, "MHCLG Ops")

    def test_admin_can_see_close_vir_button(self):
        user = get_admin_user()
        request = self.factory.get(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk])
        )
        request.user = user
        view = VisaApplicationVIRView()
        view.request = request
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        form = context.get("add_comment_form")
        self.assertIsNotNone(form)
        form = form(user_can_close_vir=True)
        button_names = [
            btn.name
            for btn in form.helper.layout.fields[-1].fields
            if hasattr(btn, "name")
        ]
        self.assertIn("close_vir_submit", button_names)

    def test_non_admin_cannot_see_close_vir_button(self):
        user = get_la_user()
        request = self.factory.get(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk])
        )
        request.user = user
        view = VisaApplicationVIRView()
        view.request = request
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        form = context.get("add_comment_form")
        self.assertIsNotNone(form)
        form = form(user_can_close_vir=False)
        button_names = [
            btn.name
            for btn in form.helper.layout.fields[-1].fields
            if hasattr(btn, "name")
        ]
        self.assertNotIn("close_vir_submit", button_names)


class VisaApplicationVIRViewReopenTests(TestCase):
    def setUp(self):
        fixed_datetime = datetime(2025, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
        self.factory = RequestFactory()
        self.visa_application = VisaApplicationFactory(
            application_unique_application_number="UAN987654321",
            ltla_name="Closed LTLA",
            utla_name="Closed UTLA",
        )
        self.person = MvPerson.objects.create(
            id="person2",
            application_number=[
                self.visa_application.application_unique_application_number
            ],
        )
        self.closed_vir = VisaInformationRequest.objects.create(
            visa_information_request_id="vir_closed",
            visa_application=self.visa_application,
            request_type=VisaInformationRequest.RequestType.GENERAL,
            requested_check_type_id=[
                VisaInformationRequest.RequestedCheckType.ACCOMM_SUITABLE.value,
                VisaInformationRequest.RequestedCheckType.SPONSOR_DBS.value,
            ],
            request_status=VisaInformationRequest.RequestStatus.CLOSED,
            created_by="ukviuser",
            created_at=fixed_datetime,
            requested_at=fixed_datetime,
            closed_at=fixed_datetime,
            ltla_name="Closed LTLA",
            utla_name="Closed UTLA",
        )
        self.initial_comment = VisaInformationRequestComments.objects.create(
            id="comment_closed_1",
            visa_information_request=self.closed_vir,
            comment="Initial comment for closed VIR",
            created_at=fixed_datetime,
            created_by_uid="ukviuser",
        )

    def test_reopen_vir_button_visible_for_admin(self):
        user = get_admin_user()
        request = self.factory.get(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk])
        )
        request.user = user
        view = VisaApplicationVIRView()
        view.request = request
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        self.assertTrue(context["user_can_reopen_vir"])

    def test_reopen_vir_button_visible_for_ukvi(self):
        user = get_ukvi_user()
        request = self.factory.get(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk])
        )
        request.user = user
        view = VisaApplicationVIRView()
        view.request = request
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        self.assertTrue(context["user_can_reopen_vir"])

    def test_reopen_vir_button_not_visible_for_la(self):
        user = get_la_user()
        request = self.factory.get(
            reverse("visa-applications:detail-vir", args=[self.visa_application.pk])
        )
        request.user = user
        view = VisaApplicationVIRView()
        view.request = request
        view.object = self.visa_application
        view.kwargs = {"pk": self.visa_application.pk}
        view.get_object = lambda: view.object
        context = view.get_context_data()
        self.assertFalse(context["user_can_reopen_vir"])
