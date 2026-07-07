from ontology.models import ReassignmentRequest
from ontology.tests.base import LocalAuthorityBaseTestCaseMixin
from ontology.tests.factories import ReassignmentRequestFactory


class ReassignmentRequestDefaultManagerTest(LocalAuthorityBaseTestCaseMixin):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_to_ltla_two_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.ltla_two_a_to_ltla_one_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_two_a_name],
            source_utla_name=[self.utla_two_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

        self.ltla_one_a_ltla_two_a_to_ltla_one_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name, self.ltla_two_a_name],
            source_utla_name=[self.utla_one_name, self.utla_two_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

        self.ltla_one_a_ltla_one_b_to_ltla_two_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name, self.ltla_one_b_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.other_da_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_other_da_name],
            source_utla_name=[self.utla_other_da_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

        self.missing_source_ltla_request = ReassignmentRequestFactory(
            source_ltla_name=[],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.missing_source_utla_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name],
            source_utla_name=[],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.missing_destination_ltla_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_two_a_name],
            source_utla_name=[self.utla_two_name],
            destination_ltla_name=None,
            destination_utla_name=self.utla_one_name,
        )

        self.missing_destination_utla_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_two_a_name],
            source_utla_name=[self.utla_two_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=None,
        )

        self.unrelated_request = ReassignmentRequestFactory(
            source_ltla_name=["external_ltla"],
            source_utla_name=["external_utla"],
            destination_ltla_name="another_external_ltla",
            destination_utla_name="another_external_utla",
        )

    def test_dev_user_sees_all_requests(self):
        result = ReassignmentRequest.objects.get_for_user(self.ltla_user_dev)
        self.assertEqual(len(result), 10)

    def test_ltla_one_user_sees_ltla_one_source_or_destination_requests(self):
        result = ReassignmentRequest.objects.get_for_user(self.ltla_one_a_user)

        expected_ids = {
            str(self.ltla_one_a_to_ltla_two_a_request.id),  # src ltla_one_a
            str(self.ltla_two_a_to_ltla_one_a_request.id),  # dest ltla_one_a
            str(self.other_da_request.id),  # dest ltla_one_a
            str(self.missing_source_utla_request.id),  # src ltla_one_a
            str(self.missing_destination_utla_request.id),  # dest ltla_one_a
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la src ltla_one_a
            str(
                self.ltla_one_a_ltla_one_b_to_ltla_two_a_request.id
            ),  # multi-la src ltla_one_a and ltla_one_b
            # NOT visible:
            # self.missing_source_ltla_request (no src ltla, dest ltla_two_a)
            # self.missing_destination_ltla_request (src ltla_two_a , no dest ltla)
            # self.unrelated_request (no ltla_one_a)
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)

    def test_utla_user_sees_utla_one_source_or_destination_requests(self):
        result = ReassignmentRequest.objects.get_for_user(self.utla_one_user)

        expected_ids = {
            str(self.ltla_one_a_to_ltla_two_a_request.id),  # src utla_one
            str(self.ltla_two_a_to_ltla_one_a_request.id),  # dest utla_one
            str(self.other_da_request.id),  # dest utla_one
            str(self.missing_source_ltla_request.id),  # src utla_one
            str(self.missing_source_utla_request.id),  # src ltla_one_a under utla_one
            str(self.missing_destination_ltla_request.id),  # dest utla_one
            str(
                self.missing_destination_utla_request.id
            ),  # src ltla_one_a under utla_one
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la src ltla_one_a
            str(
                self.ltla_one_a_ltla_one_b_to_ltla_two_a_request.id
            ),  # multi-la src ltla_one_a and ltla_one_b
            # NOT visible:
            # self.unrelated_request (no utla_one involvement)
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)

    def test_da_user_sees_ltla_utla_one_and_two_source_or_destination_requests(self):
        result = ReassignmentRequest.objects.get_for_user(self.da_main_user)

        expected_ids = {
            str(self.ltla_one_a_to_ltla_two_a_request.id),
            str(self.ltla_two_a_to_ltla_one_a_request.id),
            str(self.other_da_request.id),
            str(self.missing_source_ltla_request.id),
            str(self.missing_source_utla_request.id),
            str(self.missing_destination_ltla_request.id),
            str(self.missing_destination_utla_request.id),
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la src ltla_one_a
            str(
                self.ltla_one_a_ltla_one_b_to_ltla_two_a_request.id
            ),  # multi-la src ltla_one_a and ltla_one_b
            # NOT visible:
            # self.unrelated_request (no da_main involvement)
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)


class ReassignmentRequestMadeManagerTest(LocalAuthorityBaseTestCaseMixin):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_made_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.ltla_one_b_made_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_b_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.ltla_one_a_ltla_two_a_to_ltla_one_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name, self.ltla_two_a_name],
            source_utla_name=[self.utla_one_name, self.utla_two_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

        self.ltla_one_a_ltla_one_b_to_ltla_two_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name, self.ltla_one_b_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.missing_source_ltla_made_request = ReassignmentRequestFactory(
            source_ltla_name=[],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.missing_source_utla_made_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name],
            source_utla_name=[],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.ltla_two_with_missing_source_utla_made_request = (
            ReassignmentRequestFactory(
                source_ltla_name=[self.ltla_two_a_name],
                source_utla_name=[],
                destination_ltla_name=self.ltla_other_da_name,
                destination_utla_name=self.utla_other_da_name,
            )
        )

        self.other_da_made_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_other_da_name],
            source_utla_name=[self.utla_other_da_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

        self.received_request = ReassignmentRequestFactory(
            source_ltla_name=["external_ltla"],
            source_utla_name=["external_utla"],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

    def test_dev_user_sees_all_made_requests(self):
        result = ReassignmentRequest.made.get_for_user(self.ltla_user_dev)
        self.assertEqual(len(result), 9)

    def test_ltla_user_sees_requests_made_by_their_ltla(self):
        result = ReassignmentRequest.made.get_for_user(self.ltla_one_a_user)

        expected_ids = {
            str(self.ltla_one_a_made_request.id),
            str(self.missing_source_utla_made_request.id),  # Made by ltla_one_a
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la src ltla_one_a
            str(
                self.ltla_one_a_ltla_one_b_to_ltla_two_a_request.id
            ),  # multi-la src ltla_one_a and ltla_one_b
            # NOT visible:
            # self.ltla_one_b_made_request (made by ltla_one_b, not ltla_one_a)
            # self.missing_source_ltla_made_request (made by utla_one, not ltla_one_a)
            # self.ltla_two_with_missing_source_utla_made_request (made by ltla_two_a)
            # self.other_da_made_request (made by different DA)
            # self.received_request (received by ltla_one_a, not made by)
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)

    def test_utla_user_sees_requests_made_by_utla_one_or_child_ltla(self):
        result = ReassignmentRequest.made.get_for_user(self.utla_one_user)

        expected_ids = {
            str(self.ltla_one_a_made_request.id),  # Made by utla_one
            str(self.ltla_one_b_made_request.id),  # Made by utla_one
            str(self.missing_source_ltla_made_request.id),  # Made by utla_one
            str(self.missing_source_utla_made_request.id),  # Made by child LTLA
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la src ltla_one_a
            str(
                self.ltla_one_a_ltla_one_b_to_ltla_two_a_request.id
            ),  # multi-la src ltla_one_a and ltla_one_b
            # NOT visible:
            # self.ltla_two_with_missing_source_utla_made_request (made by ltla_two_a)
            # self.other_da_made_request (made by different DA)
            # self.received_request (received by utla_one, not made by)
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)

    def test_da_user_sees_requests_made_by_child_authorities(self):
        result = ReassignmentRequest.made.get_for_user(self.da_main_user)

        expected_ids = {
            str(self.ltla_one_a_made_request.id),
            str(self.ltla_one_b_made_request.id),
            str(self.missing_source_ltla_made_request.id),
            str(self.missing_source_utla_made_request.id),
            str(self.ltla_two_with_missing_source_utla_made_request.id),
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la src ltla_one_a
            str(
                self.ltla_one_a_ltla_one_b_to_ltla_two_a_request.id
            ),  # multi-la src ltla_one_a and ltla_one_b
            # NOT visible:
            # self.other_da_made_request (made by different DA)
            # self.received_request (received by da_main, not made by)
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)


class ReassignmentRequestReceivedManagerTest(LocalAuthorityBaseTestCaseMixin):
    def setUp(self):
        super().setUp()

        self.ltla_one_a_received_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_two_a_name],
            source_utla_name=[self.utla_two_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

        self.ltla_one_b_received_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_two_a_name],
            source_utla_name=[self.utla_two_name],
            destination_ltla_name=self.ltla_one_b_name,
            destination_utla_name=self.utla_one_name,
        )

        self.ltla_one_a_ltla_two_a_to_ltla_one_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name, self.ltla_two_a_name],
            source_utla_name=[self.utla_one_name, self.utla_two_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=self.utla_one_name,
        )

        self.ltla_one_a_ltla_one_b_to_ltla_two_a_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name, self.ltla_one_b_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_two_a_name,
            destination_utla_name=self.utla_two_name,
        )

        self.missing_destination_ltla_received_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_two_a_name],
            source_utla_name=[self.utla_two_name],
            destination_ltla_name=None,
            destination_utla_name=self.utla_one_name,
        )

        self.missing_destination_utla_received_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_two_a_name],
            source_utla_name=[self.utla_two_name],
            destination_ltla_name=self.ltla_one_a_name,
            destination_utla_name=None,
        )

        self.ltla_two_missing_destination_utla_received_request = (
            ReassignmentRequestFactory(
                source_ltla_name=[self.ltla_other_da_name],
                source_utla_name=[self.utla_other_da_group],
                destination_ltla_name=self.ltla_two_a_name,
                destination_utla_name=None,
            )
        )

        self.other_da_received_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name=self.ltla_other_da_name,
            destination_utla_name=self.utla_other_da_name,
        )

        self.made_request = ReassignmentRequestFactory(
            source_ltla_name=[self.ltla_one_a_name],
            source_utla_name=[self.utla_one_name],
            destination_ltla_name="external_ltla",
            destination_utla_name="external_utla",
        )

    def test_dev_user_sees_all_received_requests(self):
        result = ReassignmentRequest.received.get_for_user(self.ltla_user_dev)
        self.assertEqual(len(result), 9)

    def test_ltla_user_sees_requests_received_by_their_ltla(self):
        result = ReassignmentRequest.received.get_for_user(self.ltla_one_a_user)

        expected_ids = {
            str(self.ltla_one_a_received_request.id),  # Received by ltla_one_a
            str(
                self.missing_destination_utla_received_request.id
            ),  # Received by ltla_one_a
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la dest ltla_one_a
            # NOT visible:
            # self.ltla_one_b_received_request (received by ltla_one_b, not ltla_one_a)
            # self.missing_destination_ltla_received_request (received by utla_one)
            # self.ltla_two_missing_destination_utla_received_request
            # self.other_da_received_request (received by other DA)
            # self.made_request (made by ltla_one_a, not received by)
            # self.ltla_one_a_ltla_one_b_to_ltla_two_a_request
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)

    def test_utla_user_sees_requests_received_by_child_ltlas(self):
        result = ReassignmentRequest.received.get_for_user(self.utla_one_user)

        expected_ids = {
            str(self.ltla_one_a_received_request.id),  # Received by utla_one
            str(self.ltla_one_b_received_request.id),  # Received by utla_one
            str(
                self.missing_destination_ltla_received_request.id
            ),  # Received by utla_one
            str(
                self.missing_destination_utla_received_request.id
            ),  # Received by Child LTLA
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la dest ltla_one_a
            # NOT visible:
            # self.ltla_two_with_missing_source_utla_made_request (received by other DA)
            # self.ltla_two_missing_destination_utla_received_request
            # self.other_da_received_request (received by other DA)
            # self.made_request (made by utla_one, not received by)
            # self.ltla_one_a_ltla_one_b_to_ltla_two_a_request
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)

    def test_da_user_sees_requests_received_by_child_authorities(self):
        result = ReassignmentRequest.received.get_for_user(self.da_main_user)

        expected_ids = {
            str(self.ltla_one_a_received_request.id),
            str(self.ltla_one_b_received_request.id),
            str(self.missing_destination_ltla_received_request.id),
            str(self.missing_destination_utla_received_request.id),
            str(self.ltla_two_missing_destination_utla_received_request.id),
            str(
                self.ltla_one_a_ltla_two_a_to_ltla_one_a_request.id
            ),  # multi-la dest ltla_one_a
            str(
                self.ltla_one_a_ltla_one_b_to_ltla_two_a_request.id
            ),  # multi-la dest ltla_one_a
            # NOT visible:
            # self.other_da_received_request (received by different DA)
            # self.made_request (made by da_main, not received by)
        }

        actual_ids = {req.id for req in result}

        self.assertEqual(actual_ids, expected_ids)
