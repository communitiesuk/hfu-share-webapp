from django import template
from django.core.paginator import Page, Paginator
from django_tables2 import LazyPaginator
from django_tables2.templatetags.django_tables2 import table_page_range

register = template.Library()


@register.filter
def govuk_page_range(page: Page, paginator: Paginator | LazyPaginator):
    if isinstance(paginator, LazyPaginator):
        return table_page_range(page, paginator)

    return paginator.get_elided_page_range(
        number=page.number,
        on_each_side=1,
        on_ends=1,
    )
