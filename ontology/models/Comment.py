import uuid

from django.db import models


class Comment(models.Model):
    id = models.TextField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_column="id",
    )
    attached_accommodation_request_id = models.ForeignKey(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
        db_column="attached_accommodation_request_id",
    )
    attached_reassignment_request_id = models.ForeignKey(
        "ontology.ReassignmentRequest",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="attached_reassignment_request_id",
    )
    created_by = models.TextField(null=True, blank=True, db_column="created_by")
    created_at = models.DateTimeField(
        null=True, blank=True, db_column="created_at", auto_now_add=True
    )
    modified_by = models.TextField(null=True, blank=True, db_column="modified_by")
    modified_date = models.DateTimeField(
        null=True, blank=True, db_column="modified_at", auto_now=True
    )
    content = models.TextField(null=True, blank=True, db_column="content")

    class Meta:
        verbose_name = "Comment"
