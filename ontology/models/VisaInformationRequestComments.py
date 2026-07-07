from django.contrib.postgres.fields import ArrayField
from django.db import models


class VisaInformationRequestComments(models.Model):
    check_id = models.TextField(null=True, blank=True, db_column="check_id")
    checks = ArrayField(models.TextField(), null=True, blank=True, db_column="checks")
    comment = models.TextField(null=True, blank=True, db_column="comment")
    comment_type = models.TextField(null=True, blank=True, db_column="comment_type")
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    created_by_organisation = models.TextField(
        null=True, blank=True, db_column="created_by_organisation"
    )
    created_by_uid = models.TextField(null=True, blank=True, db_column="created_by_uid")
    current_status = models.TextField(null=True, blank=True, db_column="current_status")
    display_name = models.TextField(null=True, blank=True, db_column="display_name")
    id = models.TextField(primary_key=True, db_column="id")
    interaction_id = models.TextField(null=True, blank=True, db_column="interaction_id")
    is_notional = models.BooleanField(null=True, blank=True, db_column="is_notional")
    previous_status = models.TextField(
        null=True, blank=True, db_column="previous_status"
    )
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )
    visa_information_request = models.ForeignKey(
        "ontology.VisaInformationRequest",
        on_delete=models.CASCADE,
        related_name="vir_comments",
        null=True,
        blank=True,
        db_column="visa_information_request_id",
        db_constraint=False,
    )

    class Meta:
        verbose_name_plural = "Visa information request comments"
