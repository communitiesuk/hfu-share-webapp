from django.contrib.auth.models import Group
from django.db import models
from django.db.models import BooleanField, ForeignKey, OneToOneField, TextField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from accounts.enums import GroupType


class GroupInfo(models.Model):
    group: OneToOneField[Group] = models.OneToOneField(Group, on_delete=models.CASCADE)

    # da fields
    da_name: TextField = models.TextField(null=True, blank=True)
    da_gss_code: TextField = models.TextField(null=True, blank=True)

    # utla fields
    utla_name: TextField = models.TextField(null=True, blank=True)
    utla_gss_code: TextField = models.TextField(null=True, blank=True)

    # ltla fields
    ltla_name: TextField = models.TextField(null=True, blank=True)
    gss_code: TextField = models.TextField(null=True, blank=True)

    # generic admin fields
    is_da: BooleanField = models.BooleanField(default=False)
    parent_da: ForeignKey = models.ForeignKey(
        "GroupInfo",
        verbose_name=_("DA"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="da_parent_of",
    )

    is_utla: BooleanField = models.BooleanField(default=False)
    parent_utla: ForeignKey = models.ForeignKey(
        "GroupInfo",
        verbose_name=_("UTLA"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utla_parent_of",
    )

    description: TextField = models.TextField(null=True, blank=True)
    group_type: TextField = models.TextField(choices=GroupType.choices)

    def __str__(self):
        return f"Group info for {self.group.name}"

    class Meta:
        verbose_name = "Group info"
        verbose_name_plural = "Group info"


@receiver(post_save, sender=Group)
def create_or_update_group_info(sender, instance, created, **kwargs):
    GroupInfo.objects.get_or_create(group=instance)
