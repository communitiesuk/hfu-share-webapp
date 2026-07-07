from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(
        max_length=34,
        null=False,
        blank=False,
        help_text="Enter a title (max 34 characters)",
    )
    body = models.TextField(
        max_length=500,
        null=False,
        blank=False,
        help_text="Enter the announcement body (max 500 characters)",
    )
    type = models.CharField(
        max_length=25,
        null=True,
        blank=True,
        help_text="Optional: Type or category of announcement (max 25 characters)",
    )
    created_at = models.DateTimeField(null=False, blank=False, default=timezone.now)
    created_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        editable=False,
    )
    link = models.URLField(null=True, blank=True, help_text="Optional: Add a URL link")
    link_text = models.CharField(
        max_length=47,
        null=True,
        blank=True,
        help_text="Optional: Displayed link text to the user (max 47 characters)",
    )
    publish_at = models.DateTimeField(
        null=False,
        blank=False,
        default=timezone.now,
        help_text="Date and time of the announcement",
    )
    hidden = models.BooleanField(
        null=False,
        blank=False,
        default=False,
        help_text="Check to hide the announcement from users",
    )

    def __str__(self):
        return self.title
