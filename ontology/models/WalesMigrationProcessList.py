from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q


class WalesMigrationProcessList(models.Model):
    accommodation_id = models.TextField()
    data_index = models.IntegerField()
    date_added = models.DateTimeField()
    guest_ids = ArrayField(models.TextField())
    id = models.TextField(primary_key=True)
    input_ar_id = models.TextField()
    iteration = models.IntegerField(default=0)
    output_ar_id = models.TextField(null=True)
    reprocess = models.BooleanField(null=True, default=None)
    sponsor_id = models.TextField()
    successful_run = models.BooleanField(null=True, default=None)
    unique_application_number = ArrayField(models.TextField())
    to_close = models.BooleanField(null=False, default=False)

    @classmethod
    def get_process_list(cls):
        return cls.objects.filter(
            (Q(reprocess=True) | Q(reprocess__isnull=True))
            & (Q(successful_run=False) | Q(successful_run__isnull=True))
        )
