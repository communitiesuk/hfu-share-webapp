import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from accounts.enums import GroupType


class AccessRequestQuerySet(models.QuerySet):
    def with_related_user_details(self):
        user = get_user_model()
        return self.prefetch_related(
            Prefetch(
                "requester",
                queryset=user.objects.get_queryset(),
            ),
            Prefetch(
                "reviewer",
                queryset=user.objects.get_queryset(),
            ),
        )


class AccessRequestManager(models.Manager):
    def get_queryset(self):
        return AccessRequestQuerySet(
            self.model, using=self._db
        ).with_related_user_details()


class AccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Not reviewed")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")

    class DaGroupType(models.TextChoices):
        CENTRAL_USER = "CENTRAL_USER", _("Central user")
        LOCAL_AUTHORITY = "LOCAL_AUTHORITY", _("Local authority")

    objects = AccessRequestManager()

    reference_number = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    requester = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="requested_access"
    )
    reviewer = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="reviewed_access",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    group_type = models.TextField(choices=GroupType.choices)
    group_info = models.ForeignKey("accounts.GroupInfo", on_delete=models.CASCADE)
    da_group_type = models.TextField(choices=DaGroupType.choices, null=True, blank=True)
    justification = models.TextField()
    status = models.TextField(choices=Status.choices, default=Status.PENDING)
    rejection_justification = models.TextField(null=True, blank=True)
    hidden_by_requester = models.BooleanField(default=False)
    access_revoked = models.BooleanField(default=False)

    def group_type_label(self):
        return (
            f"{GroupType(self.group_type).label} - "
            f"{AccessRequest.DaGroupType(self.da_group_type).label}"
            if self.group_type == GroupType.DEVOLVED_ADMINISTRATION
            else GroupType(self.group_type).label
        )

    def get_initials(self) -> str:
        initials = ""

        if self.requester.first_name:
            initials += self.requester.first_name[0]

        if self.requester.last_name:
            initials += self.requester.last_name[0]

        return initials.upper()

    def get_pii_safe_record_name(self) -> str:
        return self.get_initials()

    @classmethod
    def create_access_request(
        cls,
        requester,
        group_type,
        da_group_type,
        group_info,
        justification,
    ):
        return cls.objects.create(
            requester=requester,
            group_type=group_type,
            da_group_type=da_group_type,
            group_info=group_info,
            justification=justification,
        )

    @classmethod
    def set_hidden_by_requester(cls, request_reference_number):
        request = cls.objects.get(reference_number=request_reference_number)
        request.hidden_by_requester = True
        request.save()
