import uuid

from django.db import models


class CommentAttachment(models.Model):
    id = models.TextField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_column="id",
    )
    comment = models.ForeignKey(
        "ontology.Comment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attachments",
        db_column="comment_id",
        verbose_name="Comment ID",
    )
    key = models.TextField(null=True, blank=True, db_column="key")
    media_type = models.TextField(null=True, blank=True, db_column="media_type")
    filename = models.TextField(null=True, blank=True, db_column="filename")

    class Meta:
        verbose_name = "Comment Attachment"
