from enum import StrEnum
from typing import Generic, Protocol, TypeVar

from django.db.models import Exists, OuterRef, Q, QuerySet

from accounts.enums import BROWSER_TEST_LTLA_NAMES, GroupType
from accounts.models import GroupInfo, User

# Queryset type a manager returns, so get_for_user / get_queryset keep the
# concrete queryset subtype (and its custom methods) instead of a bare QuerySet.
_QS = TypeVar("_QS", bound=QuerySet)


class DaViewerGroupNames(StrEnum):
    SCOTLAND = "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-UK_COUNTRY-Scotland"
    ENGLAND = "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-UK_COUNTRY-England"
    WALES = "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-UK_COUNTRY-Wales"
    NORTHERN_IRELAND = (
        "dluhc-PURPOSE-Resettlement_Workflow_USERS-SCOPE-UK_COUNTRY-Northern Ireland"
    )


da_group_name_to_viewer_group_name = {
    "da_england": DaViewerGroupNames.ENGLAND,
    "da_scotland": DaViewerGroupNames.SCOTLAND,
    "da_wales": DaViewerGroupNames.WALES,
    "da_northern_ireland": DaViewerGroupNames.NORTHERN_IRELAND,
}


def get_las_for_user(user: User):
    ltla_names = list(
        user.groups.values_list("groupinfo__ltla_name", flat=True).distinct()
    )

    utla_names = list(
        user.groups.filter(groupinfo__is_utla=True)
        .values_list("groupinfo__utla_name", flat=True)
        .distinct()
    )

    ltlas_within_utlas = list(
        user.groups.filter(groupinfo__is_utla=True).values_list(
            "groupinfo__utla_parent_of__ltla_name", flat=True
        )
    )

    ltla_names += ltlas_within_utlas

    da_groups = list(user.groups.filter(groupinfo__is_da=True).distinct())

    for da in da_groups:
        da_group_info = GroupInfo.objects.get(group=da)
        additional_la_groups = (
            da_group_info.da_parent_of.all()  # type: ignore[attr-defined]
        )

        additional_ltla_names = list(
            additional_la_groups.values_list("ltla_name", flat=True).distinct()
        )
        additional_utla_names = list(
            additional_la_groups.filter(is_utla=True)
            .values_list("utla_name", flat=True)
            .distinct()
        )

        ltla_names += additional_ltla_names
        utla_names += additional_utla_names

    return ltla_names, utla_names


class LocalAuthorityPermissionsManagerMixinProtocol(Protocol[_QS]):
    def get_queryset(self, *args, **kwargs) -> _QS: ...

    def get_for_user(self, user: User) -> _QS: ...

    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q: ...

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q: ...

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q: ...

    def exclude_browser_test_records(self, queryset: _QS) -> _QS: ...


class LocalAuthorityPermissionsManagerMixin(Generic[_QS]):
    def _filter_by_ltla_name(self, ltla_names: list[str]) -> Q:
        raise NotImplementedError(
            "Implement this method to take a list of ltla_names"
            "and filter your queryset down to objects within that ltla"
        )

    def _filter_by_utla_name(self, utla_names: list[str]) -> Q:
        raise NotImplementedError(
            "Implement this method to take a list of utla_names"
            "and filter your queryset down to objects within that utla"
        )

    def _filter_by_viewer_group_name(self, viewer_group_names: list[str]) -> Q:
        # Do not use where possible, this is a stop-gap to allow super sponsor records
        # to the visible
        raise NotImplementedError(
            "Implement this method to take a list of viewer_group_names"
            "and filter your queryset down to objects with that viewer group name"
        )

    def exclude_browser_test_records(
        self: "LocalAuthorityPermissionsManagerMixinProtocol[_QS]", queryset: _QS
    ) -> _QS:
        return queryset.exclude(
            pk__in=self.get_queryset()
            .filter(self._filter_by_ltla_name(BROWSER_TEST_LTLA_NAMES))
            .values("pk")
        )

    def get_all_annotate_with_user_can_view(
        self: "LocalAuthorityPermissionsManagerMixinProtocol[_QS]", user: User
    ):
        return self.get_queryset().annotate(
            user_can_view=Exists(self.get_for_user(user).filter(pk=OuterRef("pk")))
        )

    def get_for_user(
        self: "LocalAuthorityPermissionsManagerMixinProtocol[_QS]", user: User
    ) -> _QS:
        user_group_types = set(
            user.groups.values_list("groupinfo__group_type", flat=True)
        )
        # if the user belongs to a group that is not a LA/DA, return the full
        # queryset, minus records belonging to browser test local authorities.
        if user_group_types & {
            GroupType.DEV,
            GroupType.HOME_OFFICE,
            GroupType.MHCLG,
            GroupType.SERVICE_SUPPORT,
        }:
            return self.exclude_browser_test_records(self.get_queryset())

        ltla_names, utla_names = get_las_for_user(user)

        viewer_group_names = []

        da_groups = list(user.groups.filter(groupinfo__is_da=True).distinct())

        for da in da_groups:
            if da.name in da_group_name_to_viewer_group_name:
                viewer_group_names.append(
                    str(da_group_name_to_viewer_group_name[da.name])
                )

        return (
            self.get_queryset()
            .filter(
                self._filter_by_ltla_name(ltla_names)
                | self._filter_by_utla_name(utla_names)
                | self._filter_by_viewer_group_name(viewer_group_names)
            )
            .distinct()
        )
