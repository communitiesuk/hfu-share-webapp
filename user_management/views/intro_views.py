from django.views.generic import TemplateView

from webapp.mixins import PageTitleMixin, UserActionsMixin


class AccessRequestIntroView(PageTitleMixin, UserActionsMixin, TemplateView):
    # pylint: disable=view-missing-access-control
    page_heading = "Request access to data"
    heading_labels_title = False
    template_name = "user_management/access_request_form/access_request_form_intro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({"has_access": user.groups.exists()})

        return context
