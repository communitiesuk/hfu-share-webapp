from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group

from accounts.models import AccessRequest, GroupInfo, User


class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "is_active", "is_staff", "last_login"]


admin.site.register(User, CustomUserAdmin)


class GroupInfoInline(admin.StackedInline):
    model = GroupInfo
    can_delete = False
    verbose_name_plural = "Group Info"


class CustomGroupAdmin(GroupAdmin):
    list_display = [
        "name",
        "groupinfo__gss_code",
        "groupinfo__is_utla",
        "groupinfo__utla_gss_code",
    ]

    inlines = [GroupInfoInline]


class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ["requester", "group_info", "status"]
    search_fields = ["requester__email"]
    list_filter = ["status", "requester"]
    actions = [
        "set_status_to_not_reviewed",
        "set_status_to_approved",
        "set_status_to_rejected",
    ]

    def set_status_to_not_reviewed(self, request, queryset):
        queryset.update(status=AccessRequest.Status.PENDING)

    def set_status_to_approved(self, request, queryset):
        queryset.update(status=AccessRequest.Status.APPROVED)

    def set_status_to_rejected(self, request, queryset):
        queryset.update(status=AccessRequest.Status.REJECTED)


admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

admin.site.register(AccessRequest, AccessRequestAdmin)
