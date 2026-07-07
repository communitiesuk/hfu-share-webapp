from django.contrib.postgres.fields import ArrayField
from django.db import models


class SafeguardingNotification(models.Model):
    class AlertStatus(models.TextChoices):
        # deprecated, new_alert_status is to be used
        UNASSIGNED = "UNASSIGNED", ("Unassigned")
        RESOLVED = "RESOLVED", ("Resolved")
        ESCALATED = "ESCALATED", ("Escalated")
        ASSIGNED = "ASSIGNED", ("Assigned")
        DE_ESCALATED = "DE_ESCALATED", ("De-escalated")
        AUTO_RESOLVED = "AUTO_RESOLVED", ("Auto-resolved")

    class NewAlertStatus(models.TextChoices):
        UNASSIGNED = "UNASSIGNED", ("Unassigned")
        ASSIGNED = "ASSIGNED", ("Assigned")
        CLOSED = "CLOSED", ("Closed")
        ESCALATED_TO_UKVI = "ESCALATED_TO_UKVI", ("Escalated to UKVI")
        AUTO_ESCALATED_TO_UKVI = "AUTO_ESCALATED_TO_UKVI", ("Auto-escalated to UKVI")

    class AlertType(models.TextChoices):
        SAFEGUARDING_CHECK = "SAFEGUARDING_CHECK", ("Safeguarding check")
        SPONSOR_WITHDRAWN = "SPONSOR_WITHDRAWN", ("Sponsor withdrawn")

    accommodation_ids = ArrayField(
        models.TextField(), null=True, blank=True, db_column="accommodation_ids"
    )
    ar = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="ar_id",
    )
    alert_status = models.TextField(null=True, blank=True, db_column="alert_status")
    alert_type = models.TextField(null=True, blank=True, db_column="rule_name")
    applicant_gwfs = ArrayField(
        models.TextField(), null=True, blank=True, db_column="applicant_gwfs"
    )
    applicant_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="applicant_names"
    )
    applicant_person_ids = ArrayField(
        models.TextField(), null=True, blank=True, db_column="applicant_person_ids"
    )
    applicant_uans = ArrayField(
        models.TextField(), null=True, blank=True, db_column="applicant_uans"
    )
    assigned = models.TextField(null=True, blank=True, db_column="assigned")
    dev_check_v2 = models.ForeignKey(
        "ontology.DevCheckV2",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="check_id",
    )
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    description = models.TextField(null=True, blank=True, db_column="description")
    deferral_status = models.TextField(
        null=True, blank=True, db_column="deferral_status"
    )
    dluhc_id = models.TextField(null=True, blank=True, db_column="dluhc_id")
    exported_bf = models.BooleanField(null=True, blank=True, db_column="exported_bf")
    exported_ukvi = models.BooleanField(
        null=True, blank=True, db_column="exported_ukvi"
    )
    escalation_status = models.TextField(
        null=True, blank=True, db_column="escalation_status"
    )
    full_addresses = ArrayField(
        models.TextField(), null=True, blank=True, db_column="full_addresses"
    )
    id = models.TextField(primary_key=True, db_column="id")
    ltla = ArrayField(models.TextField(), null=True, blank=True, db_column="ltla")
    ltla_code = ArrayField(
        models.TextField(), null=True, blank=True, db_column="ltla_code"
    )
    modified_at = models.DateTimeField(null=True, blank=True, db_column="modified_at")
    modified_by = models.TextField(null=True, blank=True, db_column="modified_by")
    modified_by_org = models.TextField(
        null=True, blank=True, db_column="modified_by_org"
    )
    name = models.TextField(null=True, blank=True, db_column="title")
    new_alert_status = models.TextField(
        null=True, blank=True, db_column="new_alert_status"
    )
    notional_data = models.BooleanField(
        null=True, blank=True, db_column="notional_data"
    )
    rule_description = models.TextField(
        null=True, blank=True, db_column="rule_description"
    )
    sponsor_ids = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_ids"
    )
    sponsor_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="sponsor_names"
    )
    taurus_rule_id = models.TextField(null=True, blank=True, db_column="taurus_rule_id")
    updated_at = models.DateTimeField(null=True, blank=True, db_column="updated_at")
    utla = ArrayField(models.TextField(), null=True, blank=True, db_column="utla")
    utla_code = ArrayField(
        models.TextField(), null=True, blank=True, db_column="utla_code"
    )
    viewer_groups = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_groups"
    )
    visa_statuses = ArrayField(
        models.TextField(), null=True, blank=True, db_column="visa_statuses"
    )
