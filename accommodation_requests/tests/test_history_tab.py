import http.client
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import patch

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.enums import GroupType
from accounts.tests.base import TestSessionTokenMixin
from ontology.models import MvInteraction
from ontology.tests.factories import (
    AuditLogEntryFactory,
    InteractionAttachmentMetadataFactory,
    InteractionFactory,
    MvAccommodationFactory,
    MvAccommodationRequestFactory,
    MvPersonFactory,
    MvVolunteerFactory,
    SponsorshipCertificationFormFactory,
    VisaApplicationFactory,
)
from user_management.tests.base import (
    UserGroup,
    get_admin_user,
    get_da_user,
    get_la_user,
    get_mhclg_user,
    get_service_support_user,
    get_ukvi_user,
    get_user_with_groups,
)
from webapp.tests.test_s3 import S3TestCaseMixin


class AccommodationRequestHistoryTestCase(
    TestSessionTokenMixin, S3TestCaseMixin, TestCase
):
    def setUp(self):
        super().setUp()
        self.sponsor = MvVolunteerFactory(first_name="LA Sponsor", last_name="Spon")
        self.host = MvVolunteerFactory(first_name="Host", last_name="Host")
        self.guest = MvPersonFactory(first_name="LA Guest", last_name="Guest")
        self.accommodation = MvAccommodationFactory(
            ltla_name="ltla_somerset", full_address="Somerset accommodation"
        )
        self.accommodation.hosts.set([self.sponsor.id, self.host.id])
        self.uan = VisaApplicationFactory(
            ltla_name="ltla_somerset",
            application_unique_application_number="123456",
            title="Visa Application for Guest",
        )
        self.uam = SponsorshipCertificationFormFactory(
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            reference="UAM-111-222",
            given_name="John",
            family_name="Doe",
        )
        self.ar = MvAccommodationRequestFactory(
            ltla_name=["ltla_somerset"],
            utla_name=["utla_somerset"],
            accommodation_id=[self.accommodation.id],
            person_id=[self.guest.id],
            number_of_people=1,
            primary_sponsor=self.sponsor,
            sponsor_id=[self.sponsor.id],
            active_host=self.host,
            unique_application_number=[
                self.uan.application_unique_application_number,
            ],
            sponsorship_certification_number_id=[
                self.uam.pk,
            ],
        )

        self.guest.accommodation_request = self.ar
        self.guest.save()

    def test_admin_user_is_granted_access(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "History")

    def test_mhclg_user_is_granted_access(self):
        user = get_mhclg_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "History")

    def test_ukvi_user_is_granted_access(self):
        user = get_ukvi_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_service_support_user_is_granted_access(self):
        user = get_service_support_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_la_user_is_granted_access(self):
        user = get_la_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.OK)

    def test_da_user_is_denied_access(self):
        user = get_da_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, http.client.NOT_FOUND)

    def test_history_description_is_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertContains(
            response,
            "This history shows the dates a change was made to the accommodation "
            "request record on the system.",
        )

    def test_audit_logs_related_to_object_are_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.ar),
            object_pk=self.ar.pk,
            object_repr=str(self.ar),
            action=LogEntry.Action.UPDATE,
            changes={"comment": ["Old comment", "New comment"]},
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "History")
        self.assertContains(response, "Details changed")
        self.assertContains(response, f"By {user.email}")
        self.assertContains(
            response, "Comment changed: was Old comment now New comment."
        )

    def test_interactions_related_to_object_are_displayed(self):
        user = get_admin_user()
        self.client.force_login(user)

        interaction = InteractionFactory(
            created_by=user,
            linked_accommodation_request=self.ar,
            title="interaction title",
            interaction_notes="interaction content",
            created_at=timezone.now(),
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, interaction.title)
        self.assertContains(response, interaction.created_by)
        self.assertContains(response, interaction.interaction_notes)

    def test_timeline_events_are_sorted_by_date(self):
        user = get_admin_user()
        self.client.force_login(user)

        newest_interaction = InteractionFactory(
            linked_accommodation_request=self.ar,
            title="newest interaction title",
            interaction_notes="interaction content",
        )
        newest_interaction.created_at = timezone.now() + timedelta(days=1)
        newest_interaction.save()

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=user,
            content_type=ContentType.objects.get_for_model(self.ar),
            object_pk=self.ar.pk,
            object_repr=str(self.ar),
            action=LogEntry.Action.UPDATE,
            changes={"comment": ["Old comment", "New comment"]},
        )

        oldest_interaction = InteractionFactory(
            linked_accommodation_request=self.ar,
            title="oldest interaction title",
            interaction_notes="interaction content",
        )
        oldest_interaction.created_at = timezone.now() - timedelta(days=1)
        oldest_interaction.save()

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        content = response.content.decode()

        oldest_interaction_timeline_item = content.index(oldest_interaction.title)
        newest_interaction_timeline_item = content.index(newest_interaction.title)
        audit_log_timeline_item = content.index("Details changed")

        self.assertLess(newest_interaction_timeline_item, audit_log_timeline_item)
        self.assertLess(audit_log_timeline_item, oldest_interaction_timeline_item)

    def test_interaction_with_files_should_render(self):
        user = get_admin_user()
        self.client.force_login(user)

        interaction_metadata = InteractionAttachmentMetadataFactory(
            size_bytes=512,
            rid="ri.test",
            filename="custom_filename.txt",
            file_path="interaction-file-id/file.txt",
        )

        InteractionFactory(
            linked_accommodation_request=self.ar,
            title="interaction title",
            interaction_notes="interaction content",
            created_at=timezone.now(),
            attachment=interaction_metadata.rid,
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "interaction title")
        self.assertContains(response, "interaction content")
        self.assertContains(response, "Files")
        self.assertContains(response, interaction_metadata.filename)
        self.assertContains(response, "Download file")

    def test_interaction_wont_show_table_if_file_doesnt_exist_on_s3(self):
        user = get_admin_user()
        self.client.force_login(user)

        interaction_metadata = InteractionAttachmentMetadataFactory(
            size_bytes=512,
            rid="ri.test",
            filename="broken_filename.txt",
            file_path="broken",
        )

        InteractionFactory(
            linked_accommodation_request=self.ar,
            title="Interaction title",
            interaction_notes="Interaction content",
            created_at=timezone.now(),
            attachment=interaction_metadata.rid,
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertContains(response, "Interaction title")
        self.assertContains(response, "Interaction content")
        self.assertNotContains(response, interaction_metadata.filename)
        self.assertNotContains(response, "Download file")

    def test_interaction_will_only_show_file_table_for_the_right_interaction(self):
        user = get_admin_user()
        self.client.force_login(user)

        accommodation_request = MvAccommodationRequestFactory()

        interaction_metadata = InteractionAttachmentMetadataFactory(
            size_bytes=512,
            rid="ri.test",
            filename="custom_filename.txt",
            file_path="interaction-file-id/file.txt",
        )

        InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="Interaction title",
            interaction_notes="Interaction content",
            created_at=timezone.now(),
            attachment=interaction_metadata.rid,
        )

        # adding second interaction without file
        interaction_metadata_2 = InteractionAttachmentMetadataFactory(
            size_bytes=512,
            rid="ri.test2",
            filename="broken_filename.txt",
            file_path="broken",
        )

        InteractionFactory(
            linked_accommodation_request=accommodation_request,
            title="Interaction title 2",
            interaction_notes="Interaction content 2",
            created_at=timezone.now(),
            attachment=interaction_metadata_2.rid,
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[accommodation_request.pk],
            )
        )

        self.assertContains(response, "Interaction title")
        self.assertContains(response, "Interaction content")
        self.assertContains(response, interaction_metadata.filename)
        self.assertContains(response, "Download file", count=1)

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", True)
    def test_la_user_can_only_see_events_post_most_recent_reassignment(self):
        original_la_user = get_la_user()
        intermediary_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )
        final_la_user = get_user_with_groups(
            [UserGroup(name="ltla_croydon", type=GroupType.LOCAL_AUTHORITY)]
        )

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=intermediary_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Ealing",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Croydon"]
        self.ar.utla_name = ["Croydon"]
        self.ar.title = "JKL Title"
        self.ar.save()

        self.client.force_login(final_la_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 1)
        self.assertNotContains(response, "ABC Title")
        self.assertNotContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")
        self.assertContains(response, "JKL Title")

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", True)
    def test_da_user_can_only_see_events_post_most_recent_reassignment(self):
        original_la_user = get_la_user()
        intermediary_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )
        final_da_user = get_user_with_groups(
            [UserGroup(name="da_england", type=GroupType.DEVOLVED_ADMINISTRATION)]
        )

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=intermediary_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Ealing",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Croydon"]
        self.ar.utla_name = ["Croydon"]
        self.ar.title = "JKL Title"
        self.ar.save()

        self.client.force_login(final_da_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 1)
        self.assertNotContains(response, "ABC Title")
        self.assertNotContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")
        self.assertContains(response, "JKL Title")

    def test_mhclg_user_can_see_all_events(self):
        original_la_user = get_la_user()
        intermediary_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )
        request_user = get_mhclg_user()

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=intermediary_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Ealing",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Croydon"]
        self.ar.utla_name = ["Croydon"]
        self.ar.title = "JKL Title"
        self.ar.save()

        self.client.force_login(request_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 4)
        self.assertContains(response, "ABC Title")
        self.assertContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")
        self.assertContains(response, "JKL Title")

    def test_admin_user_can_see_all_events(self):
        original_la_user = get_la_user()
        intermediary_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )
        request_user = get_admin_user()

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=intermediary_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Ealing",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Croydon"]
        self.ar.utla_name = ["Croydon"]
        self.ar.title = "JKL Title"
        self.ar.save()

        self.client.force_login(request_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 4)
        self.assertContains(response, "ABC Title")
        self.assertContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")
        self.assertContains(response, "JKL Title")

    def test_ukvi_user_can_see_all_events(self):
        original_la_user = get_la_user()
        intermediary_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )
        request_user = get_ukvi_user()

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=intermediary_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Ealing",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Croydon"]
        self.ar.utla_name = ["Croydon"]
        self.ar.title = "JKL Title"
        self.ar.save()

        self.client.force_login(request_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 4)
        self.assertContains(response, "ABC Title")
        self.assertContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")
        self.assertContains(response, "JKL Title")

    def test_service_support_user_can_see_all_events(self):
        original_la_user = get_la_user()
        intermediary_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )
        request_user = get_service_support_user()

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=intermediary_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Ealing",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Croydon"]
        self.ar.utla_name = ["Croydon"]
        self.ar.title = "JKL Title"
        self.ar.save()

        self.client.force_login(request_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 4)
        self.assertContains(response, "ABC Title")
        self.assertContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")
        self.assertContains(response, "JKL Title")

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", True)
    def test_la_user_can_see_events_while_reassignment_pending(self):
        original_la_user = get_la_user()
        current_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=current_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
            interaction_notes="Reassignment request from Ealing created",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.client.force_login(current_la_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 1)
        self.assertNotContains(response, "ABC Title")
        self.assertContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", True)
    def test_da_user_can_see_events_while_reassignment_pending(self):
        original_da_user = get_da_user()
        current_da_user = get_user_with_groups(
            [UserGroup(name="da_england", type=GroupType.DEVOLVED_ADMINISTRATION)]
        )

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_da_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=current_da_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
            interaction_notes="Reassignment request from Ealing created",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.client.force_login(current_da_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reassignment accepted")
        details_changed_count = response.content.decode().count("Details changed")
        self.assertEqual(details_changed_count, 1)
        self.assertNotContains(response, "ABC Title")
        self.assertContains(response, "DEF Title")
        self.assertContains(response, "GHI Title")

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", True)
    def test_la_user_cannot_see_events_post_reassignment(self):
        original_la_user = get_la_user()
        current_la_user = get_user_with_groups(
            [UserGroup(name="ltla_ealing", type=GroupType.LOCAL_AUTHORITY)]
        )

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=current_la_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
            interaction_notes="Reassignment request from Ealing created",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.client.force_login(original_la_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", True)
    def test_da_user_cannot_see_events_post_reassignment(self):
        original_da_user = get_da_user()
        current_da_user = get_user_with_groups(
            [UserGroup(name="da_england", type=GroupType.DEVOLVED_ADMINISTRATION)]
        )

        self.ar.title = "ABC Title"
        self.ar.save()
        self.ar.title = "DEF Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=original_da_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_ACCEPTED,
            interaction_notes="Accepted the reassignment request from Somerset",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.title = "GHI Title"
        self.ar.save()

        interaction = InteractionFactory(
            created_by=current_da_user,
            linked_accommodation_request=self.ar,
            title="Reassignment accepted ",
            interaction_contact=MvInteraction.InteractionContact.REASSIGNMENT_REQUEST_CREATED,
            interaction_notes="Reassignment request from Ealing created",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        self.client.force_login(original_da_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_events_show_system_display_name(self):
        request_user = get_admin_user()
        self.client.force_login(request_user)

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        by_system_count = response.content.decode().count("By System")
        self.assertEqual(by_system_count, 2)

        interaction = InteractionFactory(
            created_by=None,
            linked_accommodation_request=self.ar,
            title="Rematch required",
            interaction_contact=MvInteraction.InteractionContact.REMATCH_REQUIRED,
            interaction_notes="Rematch required triggered by system change",
        )
        interaction.created_at = timezone.now()
        interaction.save()

        AuditLogEntryFactory(
            timestamp=timezone.now(),
            actor=None,
            content_type=ContentType.objects.get_for_model(self.ar),
            object_pk=self.ar.pk,
            object_repr=str(self.ar),
            action=LogEntry.Action.UPDATE,
            changes={
                "accommodation_id": [f"{[self.accommodation.id]}", "[]"],
                "sponsor_id": [f"{[self.sponsor.id]}", "[]"],
                "checks_status": ["Checks required", "Rematch required"],
            },
        )

        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rematch required")
        self.assertContains(response, "Sponsor ID deleted")
        by_system_count = response.content.decode().count("By System")
        self.assertEqual(by_system_count, 4)

    def test_events_do_not_show_by_system_for_pre_go_live_interactions(self):
        la_user = get_la_user()
        request_user = get_admin_user()
        self.client.force_login(request_user)

        response = self.client.get(
            reverse("accommodation-requests:detail-history", args=[self.ar.pk])
        )

        by_system_count = response.content.decode().count("By System")
        self.assertEqual(by_system_count, 2)

        # interaction created by a real user
        interaction = InteractionFactory(
            created_by=la_user,
            linked_accommodation_request=self.ar,
            title="User authored interaction",
            interaction_notes="Interaction content by user",
        )
        interaction.created_at = datetime(2025, 9, 11, 12, 0, tzinfo=dt_timezone.utc)
        interaction.save()

        response = self.client.get(
            reverse("accommodation-requests:detail-history", args=[self.ar.pk])
        )

        self.assertEqual(response.status_code, 200)
        by_system_count = response.content.decode().count("By System")
        # Count remains unchanged at 2
        self.assertEqual(by_system_count, 2)

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", False)
    def test_la_user_sees_no_events_when_la_history_disabled(self):
        user = get_la_user()
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "No events")

    @patch("case_management.settings.LA_HISTORY_TAB_ENABLED", False)
    def test_da_user_sees_no_events_when_la_history_disabled(self):
        self.ar.ltla_name = ["Ealing"]
        self.ar.utla_name = ["Ealing"]
        self.ar.save()
        user = get_user_with_groups(
            [UserGroup(name="da_england", type=GroupType.DEVOLVED_ADMINISTRATION)]
        )
        self.client.force_login(user)
        response = self.client.get(
            reverse(
                "accommodation-requests:detail-history",
                args=[self.ar.pk],
            )
        )
        self.assertEqual(response.status_code, http.client.OK)
        self.assertContains(response, "No events")
