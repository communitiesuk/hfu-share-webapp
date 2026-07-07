from django.contrib import admin as django_admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from accounts.enums import GroupType
from ontology.admin_stats import generate_monthly_audit_stats, get_user_stats
from webapp.mixins import PermissionsMixin


@method_decorator(staff_member_required, name="dispatch")
class AuditlogAdminStatsView(PermissionsMixin, TemplateView):
    group_type = [GroupType.DEV]

    template_name = "webapp/pages/admin/auditlog_stats.html"

    def get_context_data(self, **kwargs):
        context = {
            **django_admin.site.each_context(self.request),
            **super().get_context_data(**kwargs),
        }
        audit_log_stats = generate_monthly_audit_stats()
        user_stats = get_user_stats()
        context["title"] = "Statistics"
        context["all_stats"] = audit_log_stats
        context["user_stats"] = user_stats
        # Pick a model to grab the months from
        context["month_names"] = audit_log_stats["MvAccommodation"].keys()

        return context
