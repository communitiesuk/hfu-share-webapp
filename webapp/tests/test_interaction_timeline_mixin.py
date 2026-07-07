from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.test import TestCase
from django.utils import timezone
from django.views.generic import DetailView

from ontology.models import MvAccommodationRequest
from ontology.tests.factories import (
    InteractionFactory,
    MvAccommodationRequestFactory,
)
from webapp.mixins import InteractionWithFilesTimelineEventsMixin


class TestTimelineView(InteractionWithFilesTimelineEventsMixin, DetailView):
    # pylint: disable=view-missing-access-control
    model = MvAccommodationRequest


class TestInteractionDateRangeView(InteractionWithFilesTimelineEventsMixin):
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


class InteractionTimelineMixinTest(TestCase):
    def setUp(self):
        self.view = TestTimelineView()

    def setup_view(self, obj, start=None, end=None, show=True):
        view = TestInteractionDateRangeView(start=start, end=end, show=show)
        view.object = obj
        return view

    def assert_event_present(self, event_dates, expected_dt):
        self.assertTrue(
            any(abs((expected_dt - d).total_seconds()) < 1 for d in event_dates)
        )

    def test_returns_interactions_linked_to_accommodation_request(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
        )
        self.view.object = accommodation_request

        interaction = InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="interaction title",
            interaction_notes="interaction content",
            created_at=timezone.now(),
        )

        events = self.view.get_timeline_events(accommodation_request)
        self.assertEqual(len(events), 1)

        timeline_event = events[0]
        self.assertEqual(timeline_event.title, interaction.title)
        self.assertEqual(timeline_event.content, interaction.interaction_notes)
        self.assertEqual(timeline_event.date, interaction.created_at)

    def test_interactions_are_date_ordered(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
        )
        self.view.object = accommodation_request

        oldest_interaction = InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="oldest title",
            interaction_notes="interaction content",
        )
        oldest_interaction.created_at = timezone.now() - timedelta(days=1)
        oldest_interaction.save()

        newest_interaction = InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="newest title",
            interaction_notes="interaction content",
        )
        newest_interaction.created_at = timezone.now() + timedelta(days=1)
        newest_interaction.save()

        events = self.view.get_timeline_events(accommodation_request)
        self.assertEqual(events[0].title, newest_interaction.title)
        self.assertEqual(events[1].title, oldest_interaction.title)

    def test_interactions_notes_are_formatted_for_timeline_content(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
        )
        self.view.object = accommodation_request

        raw_interaction_notes = (
            "Reassignment request for [names_list]firstname1 lastname1 and firstname2 "
            "lastname2.[names_list_end] from old_ltla to new_ltla."
        )

        formatted_interaction_notes = (
            "Reassignment request for <ul class='govuk-list govuk-list--bullet'>"
            "<li>firstname1 lastname1</li><li>firstname2 lastname2</li>"
            "</ul> from old_ltla to new_ltla."
        )

        interaction = InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="Interaction title",
            interaction_notes=raw_interaction_notes,
        )
        interaction.save()

        events = self.view.get_timeline_events(accommodation_request)
        self.assertEqual(len(events), 1)

        timeline_event = events[0]
        self.assertEqual(timeline_event.title, interaction.title)
        self.assertEqual(timeline_event.content, formatted_interaction_notes)

    def test_interaction_has_system_display_name_for_events_without_user(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
        )
        self.view.object = accommodation_request

        interaction = InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="Interaction title",
            interaction_notes="Note",
            created_by=None,
        )
        interaction.save()

        events = self.view.get_timeline_events(accommodation_request)
        timeline_event = events[0]
        self.assertEqual("System", timeline_event.author_display_name)

    def test_returns_events_within_date_range(self):
        ar = MvAccommodationRequestFactory()
        now = timezone.now()
        interaction1 = InteractionFactory(linked_accommodation_request=ar)
        interaction1.created_at = now - timedelta(hours=3)
        interaction1.save()
        interaction2 = InteractionFactory(linked_accommodation_request=ar)
        interaction2.created_at = now - timedelta(hours=1)
        interaction2.save()
        interaction3 = InteractionFactory(linked_accommodation_request=ar)
        interaction3.created_at = now
        interaction3.save()
        view = self.setup_view(
            ar, start=now - timedelta(hours=2), end=now + timedelta(hours=1)
        )
        events = view.get_timeline_events(ar)
        event_dates = [e.date for e in events]
        self.assert_event_present(event_dates, interaction2.created_at)
        self.assert_event_present(event_dates, interaction3.created_at)
        self.assertNotIn(interaction1.created_at, event_dates)

    def test_excludes_events_outside_date_range(self):
        ar = MvAccommodationRequestFactory()
        now = timezone.now()
        interaction1 = InteractionFactory(linked_accommodation_request=ar)
        interaction1.created_at = now - timedelta(days=2)
        interaction1.save()
        interaction2 = InteractionFactory(linked_accommodation_request=ar)
        interaction2.created_at = now - timedelta(days=1)
        interaction2.save()
        interaction3 = InteractionFactory(linked_accommodation_request=ar)
        interaction3.created_at = now
        interaction3.save()
        view = self.setup_view(
            ar, start=now + timedelta(days=1), end=now + timedelta(days=2)
        )
        events = view.get_timeline_events(ar)
        self.assertEqual(len(events), 0)

    def test_returns_no_events_when_show_events_is_false(self):
        ar = MvAccommodationRequestFactory()
        interaction = InteractionFactory(linked_accommodation_request=ar)
        interaction.created_at = timezone.now()
        interaction.save()
        view = self.setup_view(ar, show=False)
        events = view.get_timeline_events(ar)
        self.assertEqual(events, [])

    def test_interaction_before_go_live_has_no_system_display_name(self):
        accommodation_request = MvAccommodationRequestFactory(
            title="Test Accommodation Request",
        )
        self.view.object = accommodation_request

        interaction = InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="Interaction title",
            interaction_notes="Note",
            created_by=None,
        )
        interaction.created_at = datetime(2025, 9, 14, 12, 0, tzinfo=dt_timezone.utc)
        interaction.save()

        events = self.view.get_timeline_events(accommodation_request)
        timeline_event = events[0]
        self.assertIsNone(timeline_event.author_display_name)
