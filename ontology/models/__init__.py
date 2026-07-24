from django.db.models import Lookup
from django.db.models.fields import Field

from .AccommodationMasterRecord import AccommodationMasterRecord
from .Announcement import Announcement
from .CheckType import CheckType
from .Comment import Comment
from .CommentAttachment import CommentAttachment
from .CommentAttachmentMetadata import CommentAttachmentMetadata
from .DevCheckV2 import DevCheckV2
from .EoiHost import EoiHost
from .ExportToolObject import ExportToolObject
from .HiddenUnassignedAccommodationRequest import (
    HiddenUnassignedAccommodationRequest,
)
from .MvAccommodation import MvAccommodation
from .MvAccommodationRequest import MvAccommodationRequest
from .MvGroup import MvGroup
from .MvInteraction import MvInteraction
from .MvInteractionAttachmentMetadata import MvInteractionAttachmentMetadata
from .MvPerson import MvPerson
from .MvUkPostcode import MvUkPostcode
from .MvVolunteer import MvVolunteer
from .PersonMasterRecord import PersonMasterRecord
from .ReassignmentRequest import ReassignmentRequest
from .SafeguardingNotification import SafeguardingNotification
from .SafeguardingReferral import SafeguardingReferral
from .SponsorMasterRecord import SponsorMasterRecord
from .SponsorshipCertificationAttachment import SponsorshipCertificationAttachment
from .SponsorshipCertificationAttachmentMetadata import (
    SponsorshipCertificationAttachmentMetadata,
)
from .SponsorshipCertificationForm import SponsorshipCertificationForm
from .UkLocalAuthority import UkLocalAuthority
from .UprnAddress import UprnAddress
from .UserGroup import UserGroup
from .VisaApplication import VisaApplication
from .VisaInformationRequest import VisaInformationRequest
from .VisaInformationRequestComments import VisaInformationRequestComments
from .WalesMigrationProcessList import WalesMigrationProcessList


# Register the custom __any lookup
# This allows us to use the 'any' lookup in queries, e.g., field__any=array_field
@Field.register_lookup
class AnyLookup(Lookup):
    lookup_name = "any"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} = ANY{rhs}", lhs_params + rhs_params
