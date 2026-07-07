from django.db import models
from django.utils.translation import gettext_lazy as _


class GroupType(models.TextChoices):
    DEV = "DEV", _("Dev")
    LOCAL_AUTHORITY = "LOCAL_AUTHORITY", _("Local authority")
    LOCAL_AUTHORITY_EARLY_ADOPTERS = (
        "LOCAL_AUTHORITY_EARLY_ADOPTERS",
        _("Early adopters - Local authority"),
    )
    DEVOLVED_ADMINISTRATION = "DEVOLVED_ADMINISTRATION", _("Devolved administration")
    DEVOLVED_ADMINISTRATION_EARLY_ADOPTERS = (
        "DEVOLVED_ADMINISTRATION_EARLY_ADOPTERS",
        _("Early adopters - Devolved administration"),
    )
    HOME_OFFICE = "HOME_OFFICE", _("Home Office operations team")
    HOME_OFFICE_EARLY_ADOPTERS = (
        "HOME_OFFICE_EARLY_ADOPTERS",
        _("Early adopters - Home Office operations team"),
    )
    MHCLG = "MHCLG", _("MHCLG operations team")
    MHCLG_EARLY_ADOPTERS = (
        "MHCLG_EARLY_ADOPTERS",
        _("Early adopters - MHCLG operations team"),
    )
    SERVICE_SUPPORT = "SERVICE_SUPPORT", _("Service support")
    SERVICE_SUPPORT_EARLY_ADOPTERS = (
        "SERVICE_SUPPORT_EARLY_ADOPTERS",
        _("Early adopters - Service support"),
    )
