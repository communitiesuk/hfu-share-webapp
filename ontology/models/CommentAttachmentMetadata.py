from django.db import models


class CommentAttachmentMetadata(models.Model):
    id = models.TextField(primary_key=True, db_column="id")
    attachmentLocator = models.TextField(
        null=True, blank=True, db_column="attachmentLocator"
    )
    attachment_key = models.TextField(null=True, blank=True, db_column="attachment_key")
    error_message = models.TextField(null=True, blank=True, db_column="error_message")
    file_name = models.TextField(null=True, blank=True, db_column="file_name")
    file_size = models.BigIntegerField(null=True, blank=True, db_column="file_size")
    resourceId = models.TextField(null=True, blank=True, db_column="resourceId")
    s3_ETag = models.TextField(null=True, blank=True, db_column="s3_Etag")
    s3_error_message = models.TextField(
        null=True, blank=True, db_column="s3_error_message"
    )
    s3_status_code = models.TextField(null=True, blank=True, db_column="s3_status_code")
    status_code = models.IntegerField(null=True, blank=True, db_column="status_code")
    processed_timestamp = models.DateTimeField(
        null=True, blank=True, db_column="processed_timestamp"
    )

    class Meta:
        verbose_name = "Comment Attachment Metadata"
