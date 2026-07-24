from django.db import models
from django.utils import timezone


class HiddenUnassignedAccommodationRequest(models.Model):
    """Tracks which unassigned accommodation requests are to be hidden from
    the unassigned list.

    This is deliberately kept separate from the accommodation request model
    itself: hiding a request is a piece of case-working state and has nothing
    to do with the behaviour of the accommodation request.
    """

    accommodation_request = models.OneToOneField(
        "ontology.MvAccommodationRequest",
        on_delete=models.CASCADE,
        related_name="hidden_unassigned_record",
        db_column="accommodation_request_id",
    )
    hidden_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="hidden_unassigned_accommodation_requests",
    )
    hidden_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Hidden Unassigned Accommodation Request"

    def __str__(self):
        return f"Hidden: {self.accommodation_request_id}"
