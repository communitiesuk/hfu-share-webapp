from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Case, Q, Value, When
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _

from accounts.enums import GroupType


class UserQuerySet(models.QuerySet):
    def with_full_name(self):
        missing_first_name = Q(first_name__isnull=True) | Q(first_name__exact="")
        missing_last_name = Q(last_name__isnull=True) | Q(last_name__exact="")

        return self.annotate(
            full_name_or_email=Case(
                When(
                    missing_first_name | missing_last_name,
                    then="email",
                ),
                default=Concat("first_name", Value(" "), "last_name"),
                output_field=models.TextField(),
            )
        )


class CustomUserManager(UserManager):
    use_in_migrations = False

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db).with_full_name()


class User(AbstractUser):
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    email = models.EmailField(_("email address"), unique=True)
    REQUIRED_FIELDS = ["username"]  # Only used for superuser creation from the console
    entra_oid = models.UUIDField(null=True)
    entra_tid = models.UUIDField(null=True)
    first_name = models.CharField(
        _("first name"), max_length=150, blank=True, null=True
    )
    last_name = models.CharField(_("last name"), max_length=150, blank=True, null=True)

    def is_dev(self):
        return self.groups.filter(groupinfo__group_type=GroupType.DEV).exists()

    def is_la(self):
        return self.groups.filter(
            groupinfo__group_type=GroupType.LOCAL_AUTHORITY
        ).exists()

    def is_home_office(self):
        return self.groups.filter(groupinfo__group_type=GroupType.HOME_OFFICE).exists()

    def is_support(self):
        return self.groups.filter(
            groupinfo__group_type=GroupType.SERVICE_SUPPORT
        ).exists()

    def is_mhclg(self):
        return self.groups.filter(groupinfo__group_type=GroupType.MHCLG).exists()

    def is_da(self):
        return self.groups.filter(
            groupinfo__group_type=GroupType.DEVOLVED_ADMINISTRATION
        ).exists()

    def is_in_group_types(self, group_types):
        if not isinstance(group_types, (list, tuple, set)):
            group_types = [group_types]
        return self.groups.filter(groupinfo__group_type__in=group_types).exists()

    def get_initials(self) -> str:
        initials = ""

        if self.first_name:
            initials += self.first_name[0]

        if self.last_name:
            initials += self.last_name[0]

        return initials.upper()

    def get_pii_safe_record_name(self) -> str:
        return self.get_initials() or self.email[:3]

    class Meta:
        constraints = [
            models.UniqueConstraint(name="entra_id", fields=["entra_oid", "entra_tid"])
        ]
