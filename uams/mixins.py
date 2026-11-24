from ontology.models import (
    SponsorshipCertificationForm,
)
from webapp.constants import (
    LA_PRE_APPROVAL_CHECK_ALLOWED_STATUSES,
    UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE,
    UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE,
)
from webapp.mixins import PermissionsMixin


class UamsChecksMixin(PermissionsMixin):
    _can_edit_ukvi_checks: bool | None = None

    def can_edit_ukvi_checks(self):
        if self._can_edit_ukvi_checks is None:
            self._can_edit_ukvi_checks = self.user_action_allowed(
                group_types=UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE
            )

        return self._can_edit_ukvi_checks

    def can_edit_la_checks(
        self, pre_approval_status: SponsorshipCertificationForm.PreApprovalStatus
    ):
        return (
            self.user_action_allowed(group_types=UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE)
            and pre_approval_status in LA_PRE_APPROVAL_CHECK_ALLOWED_STATUSES
        )
