from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q

from ontology.mixins import LocalAuthorityPermissionsManagerMixin


class MvUkPostcodeManager(LocalAuthorityPermissionsManagerMixin, models.Manager):
    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        return Q(ltla_name__in=ltla_names)

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        return Q(utla_name__in=utla_names)

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        return Q(viewer_group_names__overlap=viewer_group_names)


class MvUkPostcode(models.Model):
    objects = MvUkPostcodeManager()

    county_code = models.TextField(null=True, db_column="county_code")
    county_name = models.TextField(null=True, db_column="county_name")
    geohash = models.TextField(null=True, db_column="geohash")
    id = models.TextField(primary_key=True, db_column="id")
    latitude = models.FloatField(null=True, db_column="latitude")
    local_authority = models.ForeignKey(
        "ontology.UkLocalAuthority",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_column="local_authority_id",
    )
    longitude = models.FloatField(null=True, db_column="longitude")
    ltla_code = models.TextField(null=True, db_column="ltla_code")
    ltla_name = models.TextField(null=True, db_column="ltla_name")
    notional_data = models.BooleanField(null=True, db_column="notional_data")
    postcode = models.TextField(null=True, db_column="postcode")
    postcode_formatted = models.TextField(null=True, db_column="postcode_formatted")
    title = models.TextField(null=True, db_column="title")
    utla_code = models.TextField(null=True, db_column="utla_code")
    utla_name = models.TextField(null=True, db_column="utla_name")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )

    def display_postcode(self):
        if self.postcode_formatted:
            return self.postcode_formatted
        if self.postcode:
            return self.postcode
        return None

    def __str__(self):
        return self.display_postcode() or "Postcode Unknown"
