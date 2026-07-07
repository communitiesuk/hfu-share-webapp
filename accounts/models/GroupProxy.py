from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Count

from user_management.templatetags.access_request_extras import (
    render_name_label_from_group,
)

# Proxy model for built-in Group model so we can adjust its manager


class GroupProxyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(user_count=Count("user"))


class GroupProxy(Group):
    objects = GroupProxyManager()

    class Meta:
        proxy = True

    def get_pii_safe_record_name(self) -> str:
        return render_name_label_from_group(self)
