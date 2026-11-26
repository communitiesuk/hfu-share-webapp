from django.template import Context, Template
from django.utils import timezone

from test_utils.base import BaseSimpleTestCase
from webapp.mixins import TimelineItem
from webapp.templatetags.timeline_extras import TimelineEventType


class TimelineTemplateTests(BaseSimpleTestCase):
    def setUp(self):
        self.event = {
            "created_at": timezone.datetime(2025, 8, 12, 17, 9),
            "title": "Test Event",
            "interaction_notes": "This is a test note.",
        }
        self.event2 = {
            "created_at": timezone.datetime(2025, 8, 13, 10, 30),
            "title": "Second Event",
            "interaction_notes": "Another note.",
        }
        self.events = [self.event, self.event2]

        self.comment_event = {
            "created_at": timezone.datetime(2025, 8, 12, 17, 9),
            "content": "This is a test comment.",
        }
        self.comment_event2 = {
            "created_at": timezone.datetime(2025, 8, 13, 10, 30),
            "content": "Another test comment.",
        }
        self.comment_events = [self.comment_event, self.comment_event2]

        self.audit_log_event = TimelineItem(
            date=timezone.datetime(2025, 8, 12, 17, 9),
            title="Details changed",
            content="First name changed: was Larry now Phil.",
            author_display_name="admin@communities.gov.uk",
        )
        self.audit_log_event2 = TimelineItem(
            date=timezone.datetime(2025, 8, 13, 10, 30),
            title="Details added",
            content="Surname added: Jones",
        )
        self.audit_log_events = [self.audit_log_event, self.audit_log_event2]

        self.request = {"path": "/accommodation-requests/test_id/interactions"}
        self.comment_request = {"path": "/accommodation-requests/test_id/comments"}
        self.audit_request = {"path": "/accommodation-requests/test_id/history"}

    def render_template(self, template_string, context):
        return Template(template_string).render(Context(context))

    def test_interactions_timeline_item_renders(self):
        template_string = """
            {% include 'webapp/components/timeline/timeline_item.html' with date=event.created_at title=event.title content=event.interaction_notes forloop=forloop %}
            """  # noqa: E501
        context = {"event": self.event, "forloop": {"counter": 1}}
        rendered = self.render_template(template_string, context)
        self.assertIn("Test Event", rendered)
        self.assertIn("This is a test note.", rendered)
        self.assertIn("12 August 2025 at 5:09pm", rendered)

    def test_enhanced_dbs_check_interaction_renders_disclosure_scotland_note(self):
        enhanced_dbs_event = {
            "created_at": timezone.datetime(2025, 8, 12, 17, 9),
            "title": "DBS check and Sponsor suitable: Enhanced DBS",
            "interaction_notes": "Enhanced DBS check: passed on 12 August 2025",
        }
        template_string = """
            {% load timeline_extras %}
            {% include 'webapp/components/timeline/timeline_item.html' with date=event.created_at title=event.title content=event.interaction_notes|format_interaction_content forloop=forloop %}
            """  # noqa: E501
        context = {"event": enhanced_dbs_event, "forloop": {"counter": 1}}
        rendered = self.render_template(template_string, context)
        self.assertIn("Enhanced DBS check: passed on 12 August 2025", rendered)
        self.assertIn(
            "(For Disclosure Scotland this refers to "
            "‘Level 2 with barred list check’.)",
            rendered,
        )

    def test_basic_dbs_check_interaction_does_not_render_disclosure_note(self):
        basic_dbs_event = {
            "created_at": timezone.datetime(2025, 8, 12, 17, 9),
            "title": "DBS check and Sponsor suitable: Basic DBS",
            "interaction_notes": "Basic DBS check: passed on 12 August 2025",
        }
        template_string = """
            {% load timeline_extras %}
            {% include 'webapp/components/timeline/timeline_item.html' with date=event.created_at title=event.title content=event.interaction_notes|format_interaction_content forloop=forloop %}
            """  # noqa: E501
        context = {"event": basic_dbs_event, "forloop": {"counter": 1}}
        rendered = self.render_template(template_string, context)
        self.assertIn("Basic DBS check: passed on 12 August 2025", rendered)
        self.assertNotIn("Disclosure Scotland", rendered)

    def test_interactions_timeline_list_renders(self):
        template_string = """
        {% include 'webapp/components/timeline/timeline_list.html' with events=events %}
        """
        context = {
            "events": self.events,
            "request": self.request,
            "event_type": TimelineEventType.INTERACTION,
        }
        rendered = self.render_template(template_string, context)
        self.assertIn("Test Event", rendered)
        self.assertIn("This is a test note.", rendered)
        self.assertIn("12 August 2025 at 5:09pm", rendered)
        self.assertIn("Second Event", rendered)
        self.assertIn("Another note.", rendered)
        self.assertIn("13 August 2025 at 10:30am", rendered)
        self.assertIn('<ol class="timeline-list" role="list">', rendered)

    def test_interactions_timeline_list_order(self):
        template_string = """
        {% include 'webapp/components/timeline/timeline_list.html' with events=events %}
        """
        context = {
            "events": self.events,
            "request": self.request,
            "event_type": TimelineEventType.INTERACTION,
        }
        rendered = self.render_template(template_string, context)
        first_event_pos = rendered.find("Test Event")
        second_event_pos = rendered.find("Second Event")
        self.assertTrue(first_event_pos < second_event_pos)

    def test_comments_timeline_item_renders(self):
        template_string = """
            {% include 'webapp/components/timeline/timeline_item.html' with date=event.created_at content=event.content forloop=forloop %}
            """  # noqa: E501
        context = {"event": self.comment_event, "forloop": {"counter": 1}}
        rendered = self.render_template(template_string, context)
        self.assertIn("This is a test comment.", rendered)
        self.assertIn("12 August 2025 at 5:09pm", rendered)

    def test_comments_timeline_list_renders(self):
        template_string = """
        {% include 'webapp/components/timeline/timeline_list.html' with events=events %}
        """
        context = {
            "events": self.comment_events,
            "request": self.comment_request,
            "event_type": TimelineEventType.COMMENT,
        }
        rendered = self.render_template(template_string, context)
        self.assertIn("This is a test comment.", rendered)
        self.assertIn("12 August 2025 at 5:09pm", rendered)
        self.assertIn("Another test comment.", rendered)
        self.assertIn("13 August 2025 at 10:30am", rendered)
        self.assertIn('<ol class="timeline-list" role="list">', rendered)

    def test_comments_timeline_list_order(self):
        template_string = """
        {% include 'webapp/components/timeline/timeline_list.html' with events=events %}
        """
        context = {
            "events": self.comment_events,
            "request": self.comment_request,
            "event_type": TimelineEventType.COMMENT,
        }
        rendered = self.render_template(template_string, context)
        first_event_pos = rendered.find("This is a test comment")
        second_event_pos = rendered.find("Another test comment")
        self.assertTrue(first_event_pos < second_event_pos)

    def test_audit_log_timeline_item_renders(self):
        template_string = """
            {% include 'webapp/components/timeline/timeline_item.html' with date=event.date title=event.title content=event.content author_display_name=event.author_display_name forloop=forloop %}
            """  # noqa: E501
        context = {"event": self.audit_log_event, "forloop": {"counter": 1}}
        rendered = self.render_template(template_string, context)
        self.assertIn("Details changed", rendered)
        self.assertIn("By admin@communities.gov.uk", rendered)
        self.assertIn("First name changed: was Larry now Phil.", rendered)
        self.assertIn("12 August 2025 at 5:09pm", rendered)

    def test_audit_log_timeline_list_renders(self):
        template_string = """
        {% include 'webapp/components/timeline/timeline_list.html' with events=events %}
        """
        context = {
            "events": self.audit_log_events,
            "request": self.audit_request,
            "event_type": TimelineEventType.LOG_ENTRY,
        }
        rendered = self.render_template(template_string, context)
        self.assertIn("Details changed", rendered)
        self.assertIn("By admin@communities.gov.uk", rendered)
        self.assertIn("First name changed: was Larry now Phil.", rendered)
        self.assertIn("12 August 2025 at 5:09pm", rendered)
        self.assertIn("Details added", rendered)
        self.assertIn("Surname added: Jones", rendered)
        self.assertIn("13 August 2025 at 10:30am", rendered)
        self.assertIn('<ol class="timeline-list" role="list">', rendered)

    def test_audit_log_timeline_item_doesnt_render_user_if_not_present(self):
        template_string = """
            {% include 'webapp/components/timeline/timeline_item.html' with date=event.date title=event.title content=event.content forloop=forloop %}
            """  # noqa: E501
        context = {"event": self.audit_log_event, "forloop": {"counter": 1}}
        rendered = self.render_template(template_string, context)
        self.assertIn("Details changed", rendered)
        self.assertNotIn("By", rendered)
        self.assertIn("First name changed: was Larry now Phil.", rendered)
        self.assertIn("12 August 2025 at 5:09pm", rendered)

    def test_audit_log_timeline_list_order(self):
        template_string = """
        {% include 'webapp/components/timeline/timeline_list.html' with events=events %}
        """
        context = {
            "events": self.audit_log_events,
            "request": self.audit_request,
            "event_type": TimelineEventType.LOG_ENTRY,
        }
        rendered = self.render_template(template_string, context)
        first_event_pos = rendered.find("Details changed")
        second_event_pos = rendered.find("Details added")
        self.assertTrue(first_event_pos < second_event_pos)
