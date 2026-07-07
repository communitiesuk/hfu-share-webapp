from django.contrib.postgres.fields import ArrayField
from django.db import models


class UkLocalAuthority(models.Model):
    checks_series = models.TextField(null=True, db_column="checks_series")
    checks_passed_series = models.TextField(null=True, db_column="checks_passed_series")
    country = models.TextField(null=True, db_column="country")
    county_code = models.TextField(null=True, db_column="county_code")
    county_name = models.TextField(null=True, db_column="county_name")
    geometry = models.TextField(null=True, db_column="geometry")
    # Array of Group IDs
    group_id = ArrayField(
        models.TextField(),
        null=True,
        db_column="group_ids",
        verbose_name="Group ID",
    )
    # The actual ManyToManyField for group IDs
    group_ids = models.ManyToManyField(
        "ontology.UserGroup", related_name="+", db_column="group_ids"
    )
    hfu_email = models.TextField(null=True, db_column="hfu_email")
    hfu_phone = models.TextField(null=True, db_column="hfu_phone")
    id = models.TextField(primary_key=True, db_column="id")
    ltla_code = models.TextField(null=True, db_column="ltla_code")
    ltla_exploration_rid = models.TextField(null=True, db_column="ltla_exploration_rid")
    ltla_name = models.TextField(null=True, db_column="ltla_name")
    notional_data = models.BooleanField(null=True, db_column="notional_data")
    org_sponsor = models.ForeignKey(
        "ontology.MvVolunteer",
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        db_column="org_sponsor_id",
    )
    uam_email = models.TextField(null=True, db_column="uam_email")
    utla_code = models.TextField(null=True, db_column="utla_code")
    utla_exploration_rid = models.TextField(null=True, db_column="utla_exploration_rid")
    utla_hfu_email = models.TextField(null=True, db_column="utla_hfu_email")
    utla_hfu_phone = models.TextField(null=True, db_column="utla_hfu_phone")
    utla_name = models.TextField(null=True, db_column="utla_name")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )
