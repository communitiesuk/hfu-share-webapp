from django.db import models


class SponsorshipCertificationAttachment(models.Model):
    created_at = models.TextField(null=True, db_column="created_at")
    form_reference = models.TextField(null=True, db_column="form_reference")
    has_been_processed = models.BooleanField(null=True, db_column="has_been_processed")
    id = models.TextField(primary_key=True, db_column="id")
    rid = models.TextField(null=True, db_column="rid")
    type = models.TextField(null=True, db_column="type")
