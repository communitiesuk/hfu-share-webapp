from datetime import date, datetime

from django.utils import timezone
from django.utils.formats import date_format

DATE_LIST_FORMAT = r"j M Y"
DATE_DETAIL_FORMAT = r"j F Y"
DATETIME_LIST_FORMAT = r"j M Y, g:ia"
DATETIME_DETAIL_FORMAT = r"j F Y \a\t g:ia"


def to_local_date(value):
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.date()
    return value


def format_date_value(value, list_view=False):
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        chosen_format = DATETIME_LIST_FORMAT if list_view else DATETIME_DETAIL_FORMAT
        return date_format(value, format=chosen_format).replace(".", "")

    if isinstance(value, date):
        chosen_format = DATE_LIST_FORMAT if list_view else DATE_DETAIL_FORMAT
        return date_format(value, format=chosen_format)

    return value
