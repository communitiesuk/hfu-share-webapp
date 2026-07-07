import datetime
import http.client

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    AuditLogEntryFactory,
    MvAccommodationFactory,
    MvVolunteerFactory,
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class SponsorsHistoryTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(
            first_name="LA Sponsor",
            last_name="Spon",
        )

        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset",
            full_address="Somerset accommodation",
        )

        self.accommodation.hosts.set([self.sponsor.id])

    def test_admin_user_is_granted_access(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, self.sponsor.first_name)
        self.assertContains(response, self.sponsor.last_name)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, self.sponsor.first_name)
        self.assertContains(response, self.sponsor.last_name)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_granted_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.client.force_login(user)
        self.scot_accommodation = MvAccommodationFactory(
            ltla_name="Aberdeenshire",
            full_address="456 Avenue",
        )
        self.scot_accommodation.hosts.set([self.sponsor.id])

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_history_description_is_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(
            response,
            "This history shows the dates a change was made to the sponsor and "
            "host record on the system.",
        )

    def test_audit_logs_related_to_object_are_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.UPDATE,
            changes={"first_name": ["Old name", "New name"]},
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

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
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.UPDATE,
            changes={
                "last_name": ["Smith", "Jones"],
                "first_name": ["Alan", "Bob"],
                "date_of_birth": ["2000-01-01", "2001-01-01"],
                "age": [25, 24],
            },
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

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
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.UPDATE,
            changes={"last_name": ["Smith", "Jones"]},
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

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
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.UPDATE,
            changes={"last_name": ["Smith", "Jones"]},
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, f"By {user.email}")

    def test_audit_logs_display_added_details_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.CREATE,
            changes={"first_name": [None, "Dave"]},
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

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
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.CREATE,
            changes={"first_name": ["Dave", None]},
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

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
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.CREATE,
            changes={
                "family_situation": ["Married", "Divorced"],
            },
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response, "Family situation changed: was Married now Divorced"
        )

    def test_audit_logs_displays_array_values_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.UPDATE,
            changes={
                "phone_number": ["[0123456789]", "[0123456789, 2345678901]"],
            },
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

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
            content_type=ContentType.objects.get_for_model(self.sponsor),
            object_pk=self.sponsor.pk,
            object_repr=str(self.sponsor),
            action=LogEntry.Action.UPDATE,
            changes={
                "flag_unsuitable": ["True", "False"],
            },
        )

        response = self.client.get(
            reverse(
                "sponsors:detail-history",
                args=[self.sponsor.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response,
            "Flag unsuitable changed: was Yes now No",
        )
