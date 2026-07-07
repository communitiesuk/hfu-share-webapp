from django.db import models


class SponsorshipCertificationAttachmentMetadata(models.Model):
    id = models.TextField(primary_key=True, db_column="id")
    sponsorship_certification_form = models.ForeignKey(
        "SponsorshipCertificationForm",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_column="sponsorship_certification_form_id",
        related_name="attachments_metadata",
        verbose_name="Sponsorship Certification Form",
    )
    type = models.TextField(null=True, blank=True, db_column="type")
    size_bytes = models.TextField(null=True, db_column="size_bytes")
    media_type = models.TextField(null=True, db_column="media_type")
    rid = models.TextField(null=True, db_column="rid")
    filename = models.TextField(null=True, db_column="filename")
    file_path = models.TextField(null=True, db_column="file_path")
    error = models.TextField(null=True, blank=True, db_column="error")
    status_code = models.TextField(null=True, blank=True, db_column="status_code")
    object_type = models.TextField(null=True, blank=True, db_column="object_type")
    attachment_property = models.TextField(
        null=True, blank=True, db_column="attachment_property"
    )

    class Meta:
        verbose_name = "Sponsorship Certification Attachment Metadata"
