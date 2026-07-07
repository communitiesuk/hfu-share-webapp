from django.db import models


class CheckType(models.Model):
    class Id(models.TextChoices):
        ACCOMM_EXISTS = "1", ("Accommodation exists")
        ACCOMM_SUITABLE = "2", ("Accommodation suitable")
        SPONSOR_DBS = "3", ("DBS check and Sponsor suitable")
        GROUP_ARRIVED = "4", ("Guests have arrived in their accommodation")
        # The following check types have been deprecated in the new system
        # We are keeping them here anyway for backwards compatibility
        SG_CHECKS_COMPLETE = ("5",)
        EOI_DBS = ("6",)
        SPONSOR_ACCEPTS_ROLE = ("7",)
        SPONSOR_ARRANGEMENTS_SUITABLE = ("8",)
        UK_FORM_UPLOADED = ("9",)
        UKR_FORM_UPLOADED = ("10",)
        HO_CHECKS_HOUSEHOLD = ("11",)
        HO_CHECKS_SPONSOR = ("12",)

    ALL_REQUIRED_CHECK_IDS = [
        Id.ACCOMM_EXISTS,
        Id.ACCOMM_SUITABLE,
        Id.SPONSOR_DBS,
        Id.GROUP_ARRIVED,
    ]

    active = models.BooleanField(null=True, db_column="active")
    check_description = models.TextField(null=True, db_column="check_description")
    id = models.TextField(primary_key=True, db_column="id", choices=Id.choices)
    check_name = models.TextField(null=True, db_column="check_name")
    is_uam = models.BooleanField(null=True, db_column="is_uam")
    linked_object = models.TextField(null=True, db_column="linked_object")
    pre_arrival = models.BooleanField(null=True, db_column="pre_arrival")

    def __str__(self):
        return CheckType.Id(self.id).label
