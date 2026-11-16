from ontology.models import (
    SponsorshipCertificationForm,
)
from webapp.constants import (
    UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE,
    UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE,
)
from webapp.mixins import PermissionsMixin


class UamsChecksMixin(PermissionsMixin):
    _can_edit_ukvi_checks: bool | None = None
    _can_edit_la_checks: bool | None = None

    def can_edit_ukvi_checks(self):
        if self._can_edit_ukvi_checks is None:
            self._can_edit_ukvi_checks = self.user_action_allowed(
                group_types=UAM_CAN_EDIT_UKVI_CHECKS_GROUP_TYPE
            )

        return self._can_edit_ukvi_checks

    def can_edit_la_checks(
        self, pre_approval_status: SponsorshipCertificationForm.PreApprovalStatus
    ):
        if self._can_edit_la_checks is None:
            self._can_edit_la_checks = self.user_action_allowed(
                group_types=UAM_CAN_EDIT_LA_CHECKS_GROUP_TYPE
            ) and pre_approval_status in [
                SponsorshipCertificationForm.PreApprovalStatus.WAITING_FOR_LA_CHECKS,
                SponsorshipCertificationForm.PreApprovalStatus.LA_CHECKS_IN_PROGRESS,
                SponsorshipCertificationForm.PreApprovalStatus.FAILED_LA_CHECKS,
                SponsorshipCertificationForm.PreApprovalStatus.PASSED_ALL_CHECKS,
                SponsorshipCertificationForm.PreApprovalStatus.COMPLETED,
            ]

        return self._can_edit_la_checks
