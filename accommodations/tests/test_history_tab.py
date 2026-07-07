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
)
from user_management.tests.base import (
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
)


class AccommodationsHistoryTestCase(TestSessionTokenMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset",
            full_address="456 Avenue",
        )

        self.accommodation.full_address = "123 Street"
        self.accommodation.save()

    def test_admin_user_is_granted_access(
        self,
    ):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "123 Street")
        self.assertContains(response, self.accommodation.full_address)

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "123 Street")
        self.assertContains(response, self.accommodation.full_address)

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_granted_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_granted_access(self):
        user = get_da_user()
        self.scot_accommodation = MvAccommodationFactory(
            ltla_name="Aberdeenshire",
            full_address="456 Avenue",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.scot_accommodation.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_history_description_is_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(
            response,
            "This history shows the dates a change was made to the "
            "accommodation record on the system.",
        )

    def test_audit_logs_related_to_object_are_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.UPDATE,
            changes={"full_address": ["Old", "New"]},
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "Address changed: was Old now New")

    def test_audit_logs_format_field_name_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.UPDATE,
            changes={
                "full_address": ["123 Street", "456 Avenue"],
                "ltla_name": [None, "Somerset"],
                "last_modified_date": ["2024-01-01", "2026-01-01"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, "Address")
        self.assertContains(response, "Lower tier LA")
        self.assertContains(response, "Last modified date")

    def test_audit_logs_display_date_and_time(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.make_aware(datetime.datetime(2025, 6, 3, 11, 30)),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.UPDATE,
            changes={
                "full_address": ["123 Street", "456 Avenue"],
                "ltla_name": [None, "Somerset"],
                "last_modified_date": ["2024-01-01", "2026-01-01"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
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
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.UPDATE,
            changes={
                "full_address": ["123 Street", "456 Avenue"],
                "ltla_name": [None, "Somerset"],
                "last_modified_date": ["2024-01-01", "2026-01-01"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, f"By {user.email}")

    def test_audit_logs_display_added_details_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.CREATE,
            changes={
                "ltla_name": [None, "Somerset"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "Lower tier LA added: now Somerset")

    def test_audit_logs_display_deleted_details_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.CREATE,
            changes={
                "ltla_name": ["Somerset", None],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "Lower tier LA deleted: was Somerset")

    def test_audit_logs_display_changed_details_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.CREATE,
            changes={
                "full_address": ["123 Street", "456 Avenue"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(response, "Address changed: was 123 Street now 456 Avenue")

    def test_audit_logs_displays_array_values_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.UPDATE,
            changes={
                "reference": ["[1234]", "[1234, 4567]"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response,
            "Reference changed: was 1234 now 1234, 4567",
        )

    def test_audit_logs_displays_boolean_values_correctly(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.accommodation),
            object_pk=self.accommodation.pk,
            object_repr=str(self.accommodation),
            action=LogEntry.Action.UPDATE,
            changes={
                "unsuitable": ["True", "False"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodations:detail-history",
                args=[self.accommodation.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response,
            "Unsuitable changed: was Yes now No",
        )
