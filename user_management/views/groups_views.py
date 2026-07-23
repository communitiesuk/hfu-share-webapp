from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Button, Div, Field, Layout, Size
from django import forms
from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.views.generic import FormView
from django_filters.filters import CharFilter
from django_filters.rest_framework import FilterSet
from django_filters.views import FilterView
from django_tables2 import LazyPaginator, SingleTableMixin, tables

from accounts.mixins import AdminAccessRequiredMixin
from accounts.models import AccessRequest, User
from accounts.models.GroupProxy import GroupProxy
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group,
)
from webapp.constants import GROUP_SEARCH_FIELDS
from webapp.mixins import (
    FilterPanelMixin,
    PIISafeRecordNameMixin,
    UserActionsMixin,
)
from webapp.search import perform_search
from webapp.views import SummaryListRow, SummaryListView


class GroupsTable(tables.Table):
    name = tables.Column()
    user_count = tables.Column(verbose_name="Count of members")

    def render_name(self, record: GroupProxy):
        return format_html(
            '<a class="govuk-link" href="{url}">{value}</a>',
            url=reverse("user-management:group-details", args=[record.pk]),
            value=render_name_label_from_group(record),
        )

    class Meta:
        model = GroupProxy
        template_name = "webapp/components/tables/table.html"
        fields = ("name", "user_count")


class GroupsFilter(FilterSet, FilterPanelMixin):
    search = CharFilter(
        label="Search",
        method="search_filter",
        help_text="Search the data in the table",
    )

    def search_filter(self, queryset, _, value):
        return perform_search(
            value,
            queryset,
            GROUP_SEARCH_FIELDS,
        )

    @property
    def form(self):
        form = super().form
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Field.text("search", label_size=Size.MEDIUM),
        )

        return form

    class Meta:
        model = GroupProxy
        fields = ["search"]


class GroupListView(AdminAccessRequiredMixin, SingleTableMixin, FilterView):
    model = GroupProxy
    table_class = GroupsTable
    filterset_class = GroupsFilter
    template_name = "user_management/groups/groups_list_page.html"
    paginator_class = LazyPaginator
    ordering = ["name"]


class GroupDetailsView(
    PIISafeRecordNameMixin, UserActionsMixin, AdminAccessRequiredMixin, SummaryListView
):
    template_name = "user_management/groups/groups_detail_view.html"
    model = GroupProxy

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formatted_group_name"] = render_name_label_from_group(self.object)
        return context

    def render_name(self, record: GroupProxy):
        return render_name_label_from_group(record)

    def render_user_set(self, value):
        users = sorted(value.all(), key=lambda user: user.email.lower())

        if len(users) == 0:
            return "No users"

        return format_html_join(
            "",
            '<div style="display: flex; justify-content: space-between;">'
            '<a href="{}" class="govuk-link govuk-link--no-underline">{}</a>'
            '<a href="{}" class="govuk-link govuk-link--no-visited-state">Remove</a>'
            "</div>",
            (
                (
                    reverse("user-management:user-details", args=[user.pk]),
                    user.email,
                    reverse(
                        "user-management:group-remove-user",
                        kwargs={"user_pk": user.pk, "group_pk": self.object.pk},
                    ),
                )
                for user in users
            ),
        )

    user_set = SummaryListRow(verbose_name="Members")

    class Meta:
        fields = [
            "name",
            "user_set",
        ]


class GroupRemoveUserForm(forms.Form):
    def __init__(self, *args, group_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Button.warning("submit", "Yes - remove this person"),
                HTML(
                    f'<a href="{
                        reverse("user-management:group-details", args=[group_pk])
                    }" class="govuk-link govuk-link--no-visited-state govuk-body">'
                    f"Cancel"
                    f"</a>"
                ),
                style="display: flex; gap: 16px; align-items: baseline",
            )
        )


class GroupRemoveUserView(UserActionsMixin, AdminAccessRequiredMixin, FormView):
    template_name = "user_management/groups/groups_remove_user_page.html"
    form_class = GroupRemoveUserForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = User.objects.get(pk=self.kwargs["user_pk"])
        context["group_name"] = render_name_label_from_group(
            GroupProxy.objects.get(pk=self.kwargs["group_pk"])
        )
        return context

    def get_success_url(self):
        return reverse("user-management:group-details", args=[self.kwargs["group_pk"]])

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
            self.request, f"{user.full_name_or_email} removed from this group."
        )
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["group_pk"] = self.kwargs["group_pk"]
        return kwargs
