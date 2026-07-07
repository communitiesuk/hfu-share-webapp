from datetime import date, datetime
from urllib import parse

from django import template
from django.db.models import QuerySet
from django.http import QueryDict
from django.shortcuts import resolve_url
from django.utils.html import format_html

from accounts.models import AccessRequest
from ontology.utils import LinkedRecordData
from webapp.constants import status_to_tag_colour

register = template.Library()


@register.filter
def is_list(value):
    return isinstance(value, (list, set, tuple, QuerySet))


@register.filter
def is_date(value):
    return isinstance(value, date) and not isinstance(value, datetime)


@register.filter
def is_datetime(value):
    return isinstance(value, datetime)


@register.filter
def is_bool(value):
    return isinstance(value, bool)


@register.filter
def dict_key(d, k):
    return d.get(k, None)


@register.filter
def is_linked_record(value):
    return hasattr(value, "display_link_data")


@register.simple_tag
def linked_record_link(value, linked_from, linked_as):
    data: LinkedRecordData = value.display_link_data(
        linked_from=linked_from, linked_as=linked_as
    )
    url = resolve_url(data.view_name, data.id)
    if data.status_type and data.status:
        tag_colour = status_to_tag_colour(data.status_type, data.status) or "grey"
        return format_html(
            '<div style="display: flex; justify-content: space-between">'
            + '<a class="govuk-link" href="{}">{}</a>'
            + '<strong class="govuk-tag govuk-tag--{}"'
            + ' style="white-space: nowrap; max-width: 100%">{}</strong>'
            + "</div>",
            url,
            data.title,
            tag_colour,
            data.status,
        )
    return format_html('<a class="govuk-link" href="{}">{}</a>', url, data.title)


@register.filter
def access_request_is_rejected(value: AccessRequest):
    return value.status == AccessRequest.Status.REJECTED


@register.filter
def access_request_is_approved(value: AccessRequest):
    return value.status == AccessRequest.Status.APPROVED


@register.filter
def ensure_list(value):
    return value if is_list(value) else [value]


@register.simple_tag
def url_replace(url, attr, val):
    (scheme, netloc, path, params, query, fragment) = parse.urlparse(url)
    query_dict = QueryDict(query).copy()
    query_dict[attr] = val
    query = query_dict.urlencode()
    return parse.urlunparse((scheme, netloc, path, params, query, fragment))


@register.simple_tag
def url_remove(url, attr):
    (scheme, netloc, path, params, query, fragment) = parse.urlparse(url)
    query_dict = QueryDict(query).copy()
    query_dict.pop(attr)
    query = query_dict.urlencode()
    return parse.urlunparse((scheme, netloc, path, params, query, fragment))
