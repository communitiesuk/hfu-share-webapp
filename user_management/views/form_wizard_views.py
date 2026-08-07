from django.shortcuts import redirect
from django.views.generic import TemplateView
from formtools.wizard.views import SessionWizardView

from accounts.enums import GroupType
from accounts.models import AccessRequest, GroupInfo
from user_management.forms import (
    AccessRequestFormDaGroupTypeStep,
    AccessRequestFormDevolvedAdministrationStep,
    AccessRequestFormGroupTypeStep,
    AccessRequestFormJustificationStep,
    AccessRequestFormLocalAuthorityStep,
    AccessRequestFormReviewStep,
)
from user_management.templatetags.access_request_extras import (
    render_name_label_from_group_info,
)
from webapp.mixins import UserActionsMixin

ACCESS_REQUEST_FORMS = [
    ("group_type", AccessRequestFormGroupTypeStep),
    ("da_group_type", AccessRequestFormDaGroupTypeStep),
    ("local_authority", AccessRequestFormLocalAuthorityStep),
    ("devolved_administration", AccessRequestFormDevolvedAdministrationStep),
    ("justification", AccessRequestFormJustificationStep),
    ("review", AccessRequestFormReviewStep),
]


ACCESS_REQUEST_TEMPLATES = {
    "group_type": "user_management/access_request_form"
    "/access_request_form_question.html",
    "da_group_type": "user_management/access_request_form"
    "/access_request_form_question.html",
    "local_authority": "user_management/access_request_form"
    "/access_request_form_question.html",
    "devolved_administration": "user_management/access_request_form"
    "/access_request_form_question.html",
    "justification": "user_management/access_request_form"
    "/access_request_form_question.html",
    "review": "user_management/access_request_form/access_request_form_review.html",
}


ACCESS_REQUEST_FORM_TITLES = {
    "group_type": "Select user group",
    "da_group_type": "Select user group",
    "local_authority": "Local authority",
    "devolved_administration": "Devolved administration: central user",
    "justification": "Tell us why you need access",
    "review": "Check your answers",
}

ACCESS_REQUEST_FORM_BREADCRUMBS = {
    "group_type": [{"name": "Select user group"}],
    "da_group_type": [{"name": "Select user group"}],
    "local_authority": [
        {"name": "Select user group", "url": "user-management:access-request-form"},
        {"name": "Local authority"},
    ],
    "devolved_administration": [
        {"name": "Select user group", "url": "user-management:access-request-form"},
        {"name": "Devolved administration: central user"},
    ],
    "justification": [{"name": "Tell us why you need access"}],
    "review": [{"name": "Check your answers"}],
    "confirmation": [{"name": "Request submitted"}],
    "your_request": [{"name": "Your request"}],
}


def show_da_group_type_step(wizard):
    group_type_data = wizard.get_cleaned_data_for_step("group_type") or {}
    group_type = group_type_data.get("group_type")
    return group_type == GroupType.DEVOLVED_ADMINISTRATION


def show_local_authority_step(wizard):
    group_type_data = wizard.get_cleaned_data_for_step("group_type") or {}
    group_type = group_type_data.get("group_type")

    if group_type == GroupType.DEVOLVED_ADMINISTRATION:
        da_group_type_data = wizard.get_cleaned_data_for_step("da_group_type") or {}
        da_group_type = da_group_type_data.get("da_group_type")
        return da_group_type == AccessRequest.DaGroupType.LOCAL_AUTHORITY

    return group_type == GroupType.LOCAL_AUTHORITY


def show_devolved_administration_step(wizard):
    group_type_data = wizard.get_cleaned_data_for_step("group_type") or {}
    group_type = group_type_data.get("group_type")

    if group_type != GroupType.DEVOLVED_ADMINISTRATION:
        return False

    da_group_type_data = wizard.get_cleaned_data_for_step("da_group_type") or {}
    da_group_type = da_group_type_data.get("da_group_type")

    return da_group_type == AccessRequest.DaGroupType.CENTRAL_USER


ACCESS_REQUEST_FORMS_CONDITIONAL_DICT = {
    "da_group_type": show_da_group_type_step,
    "local_authority": show_local_authority_step,
    "devolved_administration": show_devolved_administration_step,
}


class AccessRequestFormWizard(UserActionsMixin, SessionWizardView):  # pylint: disable=view-missing-access-control
    def get_template_names(self):
        return [ACCESS_REQUEST_TEMPLATES[self.steps.current]]

    # pylint: disable=arguments-differ
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        group_type_data = self.get_cleaned_data_for_step("group_type") or {}
        is_devolved_administration = (
            group_type_data.get("group_type") == GroupType.DEVOLVED_ADMINISTRATION
        )

        if self.steps.current == "local_authority" and is_devolved_administration:
            context["title"] = "Devolved administration: local authority"
            context["breadcrumbs"] = [
                {
                    "name": "Select user group",
                    "url": "user-management:access-request-form",
                },
                {"name": "Devolved administration: local authority"},
            ]
        else:
            context["breadcrumbs"] = ACCESS_REQUEST_FORM_BREADCRUMBS.get(
                self.steps.current
            )
            context["title"] = ACCESS_REQUEST_FORM_TITLES.get(self.steps.current)

        def get_cleaned_value(step, field):
            data = self.get_cleaned_data_for_step(step) or {}
            return data.get(field)

        if self.steps.current == "review":
            group_type = get_cleaned_value("group_type", "group_type")
            da_group_type = (
                get_cleaned_value("da_group_type", "da_group_type")
                if show_da_group_type_step(self)
                else None
            )
            local_authority = (
                get_cleaned_value("local_authority", "local_authority")
                if show_local_authority_step(self)
                else None
            )
            devolved_administration = (
                get_cleaned_value("devolved_administration", "devolved_administration")
                if show_devolved_administration_step(self)
                else None
            )

            form_data = {
                "requester": {
                    "question": "Name",
                    "answer": self.request.user.full_name_or_email,
                    "editable": False,
                },
                "group_type": {
                    "question": (
                        "Choose level of permissions"
                        if group_type in [GroupType.MHCLG, GroupType.SERVICE_SUPPORT]
                        else "User group"
                    ),
                    "answer": (
                        f"{GroupType.DEVOLVED_ADMINISTRATION.label} - "
                        f"{AccessRequest.DaGroupType(da_group_type).label.lower()}"
                        if da_group_type
                        else GroupType(group_type).label
                    ),
                    "editable": True,
                },
            }

            if local_authority:
                form_data["local_authority"] = {
                    "question": (
                        "Devolved administration"
                        if group_type == GroupType.DEVOLVED_ADMINISTRATION
                        else "Local authority"
                    ),
                    "answer": render_name_label_from_group_info(local_authority),
                    "editable": True,
                }

            if devolved_administration:
                form_data["devolved_administration"] = {
                    "question": "Devolved administration",
                    "answer": render_name_label_from_group_info(
                        devolved_administration
                    ),
                    "editable": True,
                }

            form_data["justification"] = {
                "question": "Tell us why you need access",
                "answer": get_cleaned_value("justification", "justification"),
                "editable": True,
            }

            context["form_data"] = form_data
        return context

    def done(self, form_list, **kwargs):
        cleaned_data = self.get_all_cleaned_data()
        group_type = cleaned_data.get("group_type")

        if group_type == GroupType.LOCAL_AUTHORITY:
            access_request = AccessRequest.create_access_request(
                requester=self.request.user,
                group_type=group_type,
                da_group_type=None,
                group_info=cleaned_data.get("local_authority", "local_authority"),
                justification=cleaned_data.get("justification"),
            )

        elif group_type == GroupType.DEVOLVED_ADMINISTRATION:
            da_group_type = cleaned_data.get("da_group_type")
            group_info = (
                cleaned_data.get("local_authority", "local_authority")
                if da_group_type == AccessRequest.DaGroupType.LOCAL_AUTHORITY
                else cleaned_data.get(
                    "devolved_administration", "devolved_administration"
                )
            )

            access_request = AccessRequest.create_access_request(
                requester=self.request.user,
                group_type=group_type,
                da_group_type=da_group_type,
                group_info=group_info,
                justification=cleaned_data.get("justification"),
            )

        else:
            group_info = GroupInfo.objects.get(group_type=group_type)
            access_request = AccessRequest.create_access_request(
                requester=self.request.user,
                group_type=group_type,
                da_group_type=None,
                group_info=group_info,
                justification=cleaned_data.get("justification"),
            )

        self.request.session["latest_access_request_group_name"] = (
            render_name_label_from_group_info(access_request.group_info)
        )

        return redirect("user-management:access-request-confirmation")


class AccessRequestFormConfirmationPageView(TemplateView):  # pylint: disable=view-missing-access-control
    model = AccessRequest
    template_name = (
        "user_management/access_request_form/access_request_form_confirmation.html"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = ACCESS_REQUEST_FORM_BREADCRUMBS.get("confirmation")
        context["group_name"] = self.request.session.pop(
            "latest_access_request_group_name", None
        )
        return context
