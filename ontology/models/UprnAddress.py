from django.contrib.postgres.fields import ArrayField
from django.db import models


class UprnAddress(models.Model):
    building_name = models.TextField(null=True, db_column="building_name")
    building_number = models.TextField(null=True, db_column="building_number")
    change_code = models.TextField(null=True, db_column="change_code")
    classification_code = models.TextField(null=True, db_column="classification_code")
    delivery_point_suffix = models.TextField(
        null=True, db_column="delivery_point_suffix"
    )
    easting = models.TextField(null=True, db_column="easting")
    island = models.TextField(null=True, db_column="island")
    last_update_date = models.DateField(null=True, db_column="last_update_date")
    latitude = models.FloatField(null=True, db_column="latitude")
    local_authority_id = models.TextField(null=True, db_column="local_authority_id")
    locality = models.TextField(null=True, db_column="locality")
    longitude = models.FloatField(null=True, db_column="longitude")
    ltla_name = models.TextField(null=True, db_column="ltla_name")
    northing = models.TextField(null=True, db_column="northing")
    organisation = models.TextField(null=True, db_column="organisation")
    parent_uprn = models.TextField(null=True, db_column="parent_uprn")
    po_box = models.TextField(null=True, db_column="po_box")
    post_town = models.TextField(null=True, db_column="post_town")
    postcode = models.TextField(null=True, db_column="postcode")
    rpc = models.IntegerField(null=True, db_column="rpc")
    single_line_address = models.TextField(null=True, db_column="single_line_address")
    street_name = models.TextField(null=True, db_column="street_name")
    sub_building = models.TextField(null=True, db_column="sub_building")
    toid = models.TextField(null=True, db_column="toid")
    town_name = models.TextField(null=True, db_column="town_name")
    udprn = models.TextField(null=True, db_column="udprn")
    uprn = models.TextField(primary_key=True, db_column="uprn")
    usrn = models.TextField(null=True, db_column="usrn")
    utla_name = models.TextField(null=True, db_column="utla_name")
    viewer_group_names = ArrayField(
        models.TextField(), null=True, db_column="viewer_group_names"
    )
