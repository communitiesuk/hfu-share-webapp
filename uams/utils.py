from django.conf import settings

from accounts.enums import GroupType

# Helper methods to get group types based on feature flag


# TODO: Remove when releasing the feature to all
def uam_check_group_types(group_type):
    if settings.UAM_CHECKS_ENABLED:
        return group_type

    return {
        GroupType.DEV,
    }
