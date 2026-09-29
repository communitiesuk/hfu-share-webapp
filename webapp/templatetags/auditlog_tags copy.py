# Copied from https://github.com/jazzband/django-auditlog/blob/master/auditlog/templates/auditlog

from auditlog.render import render_logentry_changes_html as render_changes
from django import template

register = template.Library()


@register.filter
def render_logentry_changes_html(log_entry):
    """
    Format LogEntry changes as HTML.

    Usage in template:
    {{ log_entry_object|render_logentry_changes_html|safe }}
    """
    return render_changes(log_entry)
