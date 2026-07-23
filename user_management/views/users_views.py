import os

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout, Size
from django import forms
from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.views.generic import FormView
from django_filters import CharFilter, FilterSet
from django_filters.views import FilterView
from django_tables2 import Column, LazyPaginator, SingleTableMixin, tables

from accounts.mixins import AdminAccessRequiredMixin
from accounts.models import AccessRequest, User
from accounts.models.GroupProxy import GroupProxy
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group,
)
from webapp.constants import USERS_SEARCH_FIELDS
from webapp.mixins import (
    FilterPanelMixin,
    PIISafeRecordNameMixin,
    UserActionsMixin,
)
from webapp.search import perform_search
from webapp.views import SummaryListView


class UsersTable(tables.Table):
    full_name_or_email = Column(verbose_name="Name")
    email = Column(verbose_name="Email")

    def render_full_name_or_email(self, record: User, value):
        return format_html(
            '<a class="govuk-link" href="{url}">{value}</a>',
            url=reverse("user-management:user-details", args=[record.pk]),
            value=value,
        )

    class Meta:
        model = User
        template_name = "webapp/components/tables/table.html"
        fields = (
            "full_name_or_email",
            "email",
        )


class UsersFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(value, queryset, USERS_SEARCH_FIELDS)

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
        )
        return form

    class Meta:
        model = User
        fields = [
            "search",
        ]


class UserListView(AdminAccessRequiredMixin, SingleTableMixin, FilterView):
    model = User
    table_class = UsersTable
    filterset_class = UsersFilter
    table_pagination = {"per_page": os.environ.get("PAGINATION_PAGE_SIZE")}
    paginator_class = LazyPaginator
    template_name = "user_management/users/users_list_page.html"
    ordering = ["full_name_or_email"]


class UserDetailsView(
    PIISafeRecordNameMixin, UserActionsMixin, AdminAccessRequiredMixin, SummaryListView
):
    template_name = "user_management/users/users_detail_view.html"
    model = User

    def render_groups(self, value):
        user_groups = sorted(list(value.all()), key=render_name_label_from_group)

        if len(user_groups) == 0:
            return "No groups"

        return format_html_join(
            "",
            '<div style="display: flex; justify-content: space-between;">'
            '<a href="{}" class="govuk-link govuk-link--no-underline">{}</a>'
            '<a href="{}" class="govuk-link govuk-link--no-visited-state">Remove</a>'
            "</div>",
            (
                (
                    reverse("user-management:group-details", args=[group.pk]),
                    render_name_label_from_group(group),
                    reverse(
                        "user-management:user-remove-from-group",
                        kwargs={"user_pk": self.object.pk, "group_pk": group.pk},
                    ),
                )
                for group in user_groups
            ),
        )

    class Meta:
        fields = [
            "first_name",
            "last_name",
            "email",
            "last_login",
            "date_joined",
            "groups",
        ]
        label_overrides = {
            "email": "Email",
            "last_login": "Date and time of last login",
            "date_joined": "Date and time when user account was created",
            "groups": "Security groups",
        }


class UserRemoveGroupForm(forms.Form):
    def __init__(self, *args, user_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Button.warning("submit", "Yes - remove this person"),
                HTML(
                    f'<a href="{
                        reverse("user-management:user-details", args=[user_pk])
                    }" class="govuk-link govuk-link--no-visited-state govuk-body">'
                    f"Cancel"
                    f"</a>"
                ),
                style="display: flex; gap: 16px; align-items: baseline",
            )
        )


class UserRemoveGroupView(AdminAccessRequiredMixin, FormView):
    template_name = "user_management/users/users_remove_group_page.html"
    form_class = UserRemoveGroupForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user_pk"] = self.kwargs["user_pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = User.objects.get(pk=self.kwargs["user_pk"])
        context["group_name"] = render_name_label_from_group(
            GroupProxy.objects.get(pk=self.kwargs["group_pk"])
        )
        return context

    def get_success_url(self):
        return reverse(
            "user-management:user-details",
            args=[self.kwargs["user_pk"]],
        )

    def form_valid(self, form):
        group = GroupProxy.objects.get(pk=self.kwargs["group_pk"])
        user = User.objects.get(pk=self.kwargs["user_pk"])

        user.groups.remove(group)
        related_approved_access_request = AccessRequest.objects.filter(
            requester=user,
            group_info__group=group,
            status=AccessRequest.Status.APPROVED,
        )
        related_approved_access_request.update(access_revoked=True)

        messages.success(
            self.request,
            f"User removed from {render_name_label_from_group(group)}",
        )
        return super().form_valid(form)
