from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import (
    Q,
)
from django.utils.translation import gettext_lazy as _

from ontology.mixins import LocalAuthorityPermissionsManagerMixin
from ontology.models.CheckType import CheckType


class VisaInformationRequestManager(
    LocalAuthorityPermissionsManagerMixin, models.Manager
):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("visa_application")
            .exclude(is_notional=True)
        )

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(visa_application__ltla_name__in=ltla_names)

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(visa_application__utla_name__in=utla_names)

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)

    def is_open(self):
        """
        Returns queryset of open VisaInformationRequest records.
        """
        return self.get_queryset().exclude(
            request_status=VisaInformationRequest.RequestStatus.CLOSED
        )


class VisaInformationRequest(models.Model):
    class RequestType(models.TextChoices):
        GENERAL = "General", _("General")
        CHILD_SPONSORED_BY_PARENTS = (
            "Child Sponsored by Parent",
            _("Child sponsored by parents"),
        )

    class RequestedCheckType(models.TextChoices):
        ACCOMM_SUITABLE = "2", _("Accommodation suitable")
        SPONSOR_DBS = "3", _("DBS check and Sponsor suitable")

    class RequestStatus(models.TextChoices):
        AWAITING_UKVI = "Awaiting UKVI", _("Awaiting UKVI")
        AWAITING_LA = "Awaiting LA", _("Awaiting LA")
        CLOSED = "Closed", _("Closed")

    objects = VisaInformationRequestManager()

    bulk_foreign_key = models.TextField(
        null=True, blank=True, db_column="bulk_foreign_key"
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    created_by = models.TextField(null=True, blank=True, db_column="created_by")
    forwarded_to_dluhc = models.BooleanField(
        null=True, blank=True, db_column="forwarded_to_dluhc"
    )
    is_notional = models.BooleanField(null=True, blank=True, db_column="is_notional")
    ltla_name = models.TextField(null=True, blank=True, db_column="ltla_name")
    modified_at = models.DateTimeField(null=True, blank=True, db_column="modified_at")
    modified_by = models.TextField(null=True, blank=True, db_column="modified_by")
    request_details = models.TextField(
        null=True, blank=True, db_column="request_details"
    )
    request_status = models.TextField(
        null=True,
        blank=True,
        db_column="request_status",
        choices=RequestStatus.choices,
    )
    request_title = models.TextField(null=True, blank=True, db_column="request_title")
    request_type = models.TextField(
        null=True,
        blank=True,
        db_column="request_type",
        choices=RequestType.choices,
    )
    requested_at = models.DateTimeField(null=True, blank=True, db_column="requested_at")
    requested_check_type_id = ArrayField(
        models.TextField(choices=CheckType.Id.choices),
        null=True,
        blank=True,
        db_column="requested_check_type_id",
    )
    utla_name = models.TextField(null=True, blank=True, db_column="utla_name")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
    visa_application = models.ForeignKey(
        "ontology.VisaApplication",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="visa_application",
        db_constraint=False,
    )
    visa_information_request_id = models.TextField(
        primary_key=True, db_column="visa_information_request_id"
    )
