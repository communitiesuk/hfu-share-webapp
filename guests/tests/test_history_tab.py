import datetime
import http.client
from datetime import date

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from accounts.tests.factories import GroupFactory
from ontology.models import MvPerson
from ontology.tests.factories import (
    AuditLogEntryFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_early_adopter_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class GuestDetailHistoryViewTests(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.accommodation_request = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            person_id=["person-2"],
            number_of_people=1,
        )
        self.guest = MvPersonFactory(
            pk="person-2",
            first_name="UPE",
            last_name="Test",
            date_of_birth=date(1991, 6, 20),
            upe_visa_status="UPE_VISA_ACCEPTED",
            accommodation_request=self.accommodation_request,
        )
        self.history_url = reverse(
            "guests:detail-history", kwargs={"pk": self.guest.pk}
        )
        self.ltla_group = GroupFactory(
            name="ltla_somerset",
            groupinfo__ltla_name="ltla_somerset",
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY,
        )

    def test_dev_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "History")
        self.assertContains(response, self.guest.first_name)
        self.assertContains(response, self.guest.last_name)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "History")
        self.assertContains(response, self.guest.first_name)
        self.assertContains(response, self.guest.last_name)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "History")
        self.assertContains(response, self.guest.first_name)
        self.assertContains(response, self.guest.last_name)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "History")
        self.assertContains(response, self.guest.first_name)
        self.assertContains(response, self.guest.last_name)

    def test_la_user_is_denied_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_da_user_is_denied_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_la_early_adopter_user_is_denied_access(self):
        user = get_la_early_adopter_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_history_description_is_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(self.history_url)

        self.assertContains(
            response,
            "This history shows the dates a change was made to the guest record "
            "on the system.",
        )

    def test_audit_logs_related_to_object_are_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.UPDATE,
            changes={"first_name": ["Old name", "New name"]},
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "First name changed: was Old name now New name")

    def test_audit_logs_format_field_name_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.UPDATE,
            changes={
                "last_name": ["Smith", "Jones"],
                "first_name": ["Alan", "Bob"],
                "date_of_birth": ["2000-01-01", "2001-01-01"],
                "age": [25, 24],
            },
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, "Last name")
        self.assertContains(response, "First name")
        self.assertContains(response, "Date of birth")
        self.assertContains(response, "Age")

    def test_audit_logs_display_date_and_time(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.make_aware(datetime.datetime(2025, 6, 3, 11, 30)),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.UPDATE,
            changes={"last_name": ["Smith", "Jones"]},
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "3 June 2025 at 11:30am")

    def test_audit_logs_display_author_user(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.make_aware(datetime.datetime(2025, 6, 3, 11, 30)),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.UPDATE,
            changes={"last_name": ["Smith", "Jones"]},
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, f"By {user.email}")

    def test_audit_logs_display_added_details_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.CREATE,
            changes={"first_name": [None, "Dave"]},
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "First name added: now Dave")

    def test_audit_logs_display_deleted_details_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.CREATE,
            changes={"first_name": ["Dave", None]},
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "First name deleted: was Dave")

    def test_audit_logs_display_changed_details_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.CREATE,
            changes={
                "first_name": ["Charlie", "Charles"],
            },
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "First name changed: was Charlie now Charles")

    def test_audit_logs_displays_array_values_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.UPDATE,
            changes={
                "phone": ["[0123456789]", "[0123456789, 2345678901]"],
            },
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response,
            "Phone number changed: was 0123456789 now 0123456789, 2345678901",
        )

    def test_audit_logs_displays_boolean_values_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.UPDATE,
            changes={
                "disability_flag": ["True", "False"],
            },
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response,
            "Disability flag changed: was Yes now No",
        )

    def test_audit_logs_displays_choice_field_values_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.guest),
            object_pk=self.guest.pk,
            object_repr=str(self.guest),
            action=LogEntry.Action.UPDATE,
            changes={
                "upe_visa_status": [
                    MvPerson.UPEVisaStatus.NO_OUTCOME,
                    MvPerson.UPEVisaStatus.ACCEPTED,
                ],
            },
        )

        response = self.client.get(self.history_url)

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response,
            "UPE visa status changed: was No UPE visa application outcome now UPE "
            "visa accepted.",
        )
