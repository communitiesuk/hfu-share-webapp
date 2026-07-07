from datetime import datetime

from django.test import TestCase
from django.urls import reverse

from accounts.tests.base import TestSessionTokenMixin
from ontology.tests.factories import (
    CommentAttachmentFactory,
    CommentAttachmentMetadataFactory,
    CommentFactory,
    MvAccommodationRequestFactory,
)
from user_management.tests.base import get_admin_user
from webapp.mixins import SummaryListTestCaseMixin
from webapp.tests.test_s3 import S3TestCaseMixin


class AccommodationRequestCommentsTestCase(
    TestSessionTokenMixin, SummaryListTestCaseMixin, S3TestCaseMixin, TestCase
):
    def test_comment_will_only_show_file_table_for_the_right_comment(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = MvAccommodationRequestFactory()
        comment = CommentFactory(
            attached_accommodation_request_id=accommodation_request,
            content="Example comment",
            created_at=datetime.today(),
        )
        CommentAttachmentFactory(
            key="comment-key-1",
            comment_id=comment.id,
            filename="comment_displayed_name.txt",
        )
        CommentAttachmentMetadataFactory(
            id="uuid-6",
            file_name="comment_attachment.txt",
            attachment_key="comment-key-1",
        )

        # Second comment without file
        CommentFactory(
            attached_accommodation_request_id=accommodation_request,
            content="Example other comment",
            created_at=datetime.today(),
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-comments",
                args=[accommodation_request.pk],
            )
        )

        self.assertContains(response, "Example comment")
        self.assertContains(response, "Comments")
        self.assertContains(response, "Files")
        self.assertContains(response, "Example other comment")
        self.assertContains(response, "comment_displayed_name.txt")
        self.assertContains(response, "Download file", count=1)

    def test_comment_wont_show_table_if_file_doesnt_exist_on_s3(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = MvAccommodationRequestFactory()
        comment = CommentFactory(
            attached_accommodation_request_id=accommodation_request,
            created_at=datetime.today(),
        )
        CommentAttachmentFactory(
            key="broken-key",
            comment_id=comment.id,
            filename="comment_displayed_name.txt",
        )
        CommentAttachmentMetadataFactory(
            id="uuid-7",
            file_name="missing_comment_file.txt",
            attachment_key="broken-key",
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-comments",
                args=[accommodation_request.pk],
            )
        )

        self.assertNotContains(response, "comment_displayed_name.txt")
        self.assertNotContains(response, "Download file")
