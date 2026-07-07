from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from ontology.models.MvPerson import MvPerson


class SafeguardingReferral(models.Model):
    class AlertedStatus(models.TextChoices):
        ALERTED = ("Alerted", _("Alerted"))
        NOT_ALERTED = ("Not Alerted", _("Not Alerted"))
        SOME_ALERTED = ("Some Alerted", _("Some Alerted"))

    alerted_status = models.TextField(null=True, blank=True, db_column="alerted_status")
    assignee = models.TextField(null=True, blank=True, db_column="assignee")
    comments = models.TextField(null=True, blank=True, db_column="comments")
    cop_reference = models.TextField(null=True, blank=True, db_column="cop_reference")
    created_at = models.DateTimeField(null=True, blank=True, db_column="created_at")
    deferral_status = models.TextField(
        null=True, blank=True, db_column="deferral_status"
    )
    id = models.TextField(primary_key=True, db_column="id")
    included_uans = ArrayField(
        models.TextField(), null=True, blank=True, db_column="included_uans"
    )
    last_referred_at = models.DateTimeField(
        null=True, blank=True, db_column="last_referred_at"
    )
    modified_at = models.DateTimeField(null=True, blank=True, db_column="modified_at")
    modified_by = models.TextField(null=True, blank=True, db_column="modified_by")
    notional_data = models.BooleanField(
        null=True, blank=True, db_column="notional_data"
    )
    person = models.ForeignKey(
        "ontology.MvPerson",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
        db_column="person_id",
        db_constraint=False,
    )
    person_has_new_uans = models.BooleanField(
        null=True, blank=True, db_column="person_has_new_uans"
    )
    title_key = models.TextField(null=True, blank=True, db_column="title_key")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, blank=True, db_column="viewer_group_names"
    )

    def get_person(self) -> MvPerson | None:
        if self.person_id:
            return MvPerson.objects.filter(id=self.person_id).first()
        return None
