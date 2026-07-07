from datetime import timedelta

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone
from django.views.generic import DetailView

from ontology.models import MvAccommodationRequest
from ontology.tests.factories import AuditLogEntryFactory, MvAccommodationRequestFactory
from user_management.tests.base import get_admin_user
from webapp.mixins import AuditLogTimelineEventsMixin


class TestTimelineDateRangeView(AuditLogTimelineEventsMixin):
    def __init__(self, start=None, end=None, show=True):
        self._start = start
        self._end = end
        self._show = show

    def _get_timeline_start(self):
        return self._start

    def _get_timeline_end(self):
        return self._end

    def _show_events(self):
        return self._show


class TestTimelineView(AuditLogTimelineEventsMixin, DetailView):
    # pylint: disable=view-missing-access-control
    model = MvAccommodationRequest


class AuditLogTimelineMixinTest(TestCase):
    def setUp(self):
        self.view = TestTimelineView()

    def create_object(self):
        return MvAccommodationRequestFactory(
            title="Test Accommodation Request",
            status=MvAccommodationRequest.Status.ACCOMMODATION_ASSIGNED,
        )

    def create_log_entry(self, obj, timestamp, changes=None, actor=None):
        ct = ContentType.objects.get_for_model(obj)
        return AuditLogEntryFactory(
            timestamp=timestamp,
            object_pk=obj.pk,
            object_repr=str(obj),
            action=LogEntry.Action.UPDATE,
            content_type=ct,
            changes=changes or {"title": ["old", "new"]},
            actor=actor,
        )

    def setup_view(self, obj, start=None, end=None, show=True):
        view = TestTimelineDateRangeView(start=start, end=end, show=show)
        view.object = obj
        return view

    def assert_event_present(self, event_dates, expected_dt):
        self.assertTrue(
            any(abs((expected_dt - d).total_seconds()) < 1 for d in event_dates)
        )

    def test_gets_audit_log_events_related_to_object(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        events = self.view.get_timeline_events(accommodation_request)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Details changed")
        self.assertTrue("Test Accommodation Request" in events[0].content)

    def test_object_audit_log_changes_are_grouped_by_event(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        self.create_log_entry(
            accommodation_request,
            timezone.now(),
            {
                "title": ["Test Accommodation Request", "Changed Title"],
                "status": ["Accommodation assigned", "None"],
                "checks_status": ["None", "Checks required"],
            },
        )

        audit_log_count = LogEntry.objects.get_for_object(accommodation_request).count()
        timeline_events = self.view.get_timeline_events(accommodation_request)

        self.assertEqual(audit_log_count, 2)
        self.assertEqual(len(timeline_events), 2)

        timeline_events.sort(key=lambda e: e.date)
        updated_event = timeline_events[-1]

        self.assertTrue(
            "Title changed: was Test Accommodation Request now Changed Title."
            in updated_event.content
        )
        self.assertTrue(
            "Status deleted: was Accommodation assigned." in updated_event.content
        )
        self.assertTrue(
            "Checks status added: now Checks required." in updated_event.content
        )

    def test_object_audit_log_content_is_correct_for_dates(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        self.create_log_entry(
            accommodation_request,
            timezone.now(),
            {
                "confirmed_arrival_date": [
                    "None",
                    timezone.datetime(2023, 1, 3).date().isoformat(),
                ],
            },
        )

        timeline_events = self.view.get_timeline_events(accommodation_request)

        timeline_events.sort(key=lambda e: e.date)
        date_update_event = timeline_events[-1]

        self.assertTrue(
            "Confirmed arrival date added: now 3 January 2023."
            in date_update_event.content
        )

    def test_object_audit_log_content_is_correct_for_arrays(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        self.create_log_entry(
            accommodation_request,
            timezone.now(),
            {
                "primary_contact_email": [
                    "[bob@example.com]",
                    "[bob@example.com, bob2@example.com]",
                ],
            },
        )

        timeline_events = self.view.get_timeline_events(accommodation_request)

        timeline_events.sort(key=lambda e: e.date)
        array_update_event = timeline_events[-1]

        self.assertTrue(
            "Primary contact email changed: was bob@example.com"
            " now bob@example.com, bob2@example.com." in array_update_event.content
        )

    def test_object_audit_log_content_is_correct_for_boolean_values(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        self.create_log_entry(
            accommodation_request,
            timezone.now(),
            {
                "will_notify_la_central_case_flag": [
                    "False",
                    "True",
                ],
            },
        )

        timeline_events = self.view.get_timeline_events(accommodation_request)

        timeline_events.sort(key=lambda e: e.date)
        boolean_update_event = timeline_events[-1]

        self.assertTrue(
            "Will notify LA central case flag changed: was No now Yes."
            in boolean_update_event.content
        )

    def test_object_audit_log_content_is_correct_for_choice_field_values(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        self.create_log_entry(
            accommodation_request,
            timezone.now(),
            {
                "status": [
                    MvAccommodationRequest.Status.ACCOMMODATION_ASSIGNED,
                    MvAccommodationRequest.Status.ARRIVAL_CONFIRMED,
                ],
                "checks_status": [
                    MvAccommodationRequest.ChecksStatus.CHECKS_REQUIRED,
                    MvAccommodationRequest.ChecksStatus.CHECKS_COMPLETED,
                ],
                "safeguarding_status": [
                    MvAccommodationRequest.SafeguardingStatus.ACTIVE_NOTIFICATIONS,
                    MvAccommodationRequest.SafeguardingStatus.NO_NOTIFICATIONS,
                ],
            },
        )

        timeline_events = self.view.get_timeline_events(accommodation_request)

        timeline_events.sort(key=lambda e: e.date)
        choice_field_update_event = timeline_events[-1]

        self.assertTrue(
            "Status changed: was Accommodation assigned now Arrival confirmed."
            in choice_field_update_event.content
        )
        self.assertTrue(
            "Checks status changed: was Checks required now Checks completed."
            in choice_field_update_event.content
        )
        self.assertTrue(
            "Safeguarding status changed: was Active safeguarding notifications now "
            "No safeguarding notifications." in choice_field_update_event.content
        )

    def test_object_audit_log_source_user_is_included(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        user = get_admin_user()
        user.email = "admin@communities.gov.uk"
        user.save()

        self.create_log_entry(
            accommodation_request,
            timezone.now(),
            {
                "title": ["Test Accommodation Request", "Changed Title"],
                "status": ["Accommodation assigned", "None"],
                "checks_status": ["None", "Checks required"],
            },
            user,
        )

        audit_log_count = LogEntry.objects.get_for_object(accommodation_request).count()
        timeline_events = self.view.get_timeline_events(accommodation_request)

        self.assertEqual(audit_log_count, 2)
        self.assertEqual(len(timeline_events), 2)

        timeline_events.sort(key=lambda e: e.date)
        updated_event = timeline_events[-1]

        self.assertTrue(
            "Title changed: was Test Accommodation Request now Changed Title."
            in updated_event.content
        )
        self.assertEqual("admin@communities.gov.uk", updated_event.author_display_name)

    def test_audit_log_timeline_has_system_display_name_for_events_without_actor(self):
        accommodation_request = self.create_object()
        self.view.object = accommodation_request

        self.create_log_entry(
            accommodation_request,
            timezone.now(),
            actor=None,
        )

        timeline_events = self.view.get_timeline_events(accommodation_request)
        timeline_events.sort(key=lambda e: e.date)
        updated_event = timeline_events[-1]
        self.assertEqual("System", updated_event.author_display_name)

    def test_returns_events_within_date_range(self):
        obj = self.create_object()
        now = timezone.now()
        log1 = self.create_log_entry(
            obj, now - timedelta(days=2), {"title": ["old1", "new1"]}
        )
        log2 = self.create_log_entry(
            obj, now - timedelta(days=1), {"title": ["old2", "new2"]}
        )
        log3 = self.create_log_entry(obj, now, {"title": ["old3", "new3"]})
        view = self.setup_view(
            obj, start=now - timedelta(days=1, hours=1), end=now + timedelta(hours=1)
        )
        events = view.get_timeline_events(obj)
        event_dates = [e.date for e in events]
        self.assert_event_present(event_dates, log2.timestamp)
        self.assert_event_present(event_dates, log3.timestamp)
        self.assertNotIn(log1.timestamp, event_dates)

    def test_excludes_events_outside_date_range(self):
        obj = self.create_object()
        now = timezone.now()
        self.create_log_entry(obj, now - timedelta(days=2), {"title": ["old", "new"]})
        self.create_log_entry(obj, now - timedelta(days=1), {"title": ["old", "new"]})
        self.create_log_entry(obj, now, {"title": ["old", "new"]})
        view = self.setup_view(
            obj, start=now + timedelta(days=1), end=now + timedelta(days=2)
        )
        events = view.get_timeline_events(obj)
        self.assertEqual(len(events), 0)

    def test_returns_no_events_when_show_events_is_false(self):
        obj = self.create_object()
        now = timezone.now()
        self.create_log_entry(obj, now, {"title": ["old", "new"]})
        view = self.setup_view(obj, show=False)
        events = view.get_timeline_events(obj)
        self.assertEqual(events, [])
