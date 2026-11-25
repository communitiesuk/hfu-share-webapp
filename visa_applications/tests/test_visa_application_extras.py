from ontology.models.VisaInformationRequest import VisaInformationRequest
from test_utils.base import BaseSimpleTestCase
from visa_applications.templatetags.visa_application_extras import (
    get_checktype_label,
    get_requesttype_label,
    vir_status_to_tag_colour,
    visa_status_to_tag_colour,
)
from webapp.constants import (
    BLUE,
    GREEN,
    RED,
    YELLOW,
    no_vir_status,
    no_visa_status,
)


class VisaStatusToTagColourTests(BaseSimpleTestCase):
    def test_returns_tag_colour_for_known_status(self):
        self.assertEqual(visa_status_to_tag_colour("Arrived"), GREEN)
        self.assertEqual(visa_status_to_tag_colour("Refused"), RED)

    def test_returns_default_tag_colour_for_unknown_status(self):
        self.assertEqual(
            visa_status_to_tag_colour("Not a real status"),
            no_visa_status.tag_colour,
        )

    def test_returns_default_tag_colour_for_none(self):
        self.assertEqual(visa_status_to_tag_colour(None), no_visa_status.tag_colour)


class VirStatusToTagColourTests(BaseSimpleTestCase):
    def test_returns_tag_colour_for_known_status_label(self):
        awaiting_ukvi = VisaInformationRequest.RequestStatus.AWAITING_UKVI.label
        awaiting_la = VisaInformationRequest.RequestStatus.AWAITING_LA.label
        closed = VisaInformationRequest.RequestStatus.CLOSED.label

        self.assertEqual(vir_status_to_tag_colour(awaiting_ukvi), YELLOW)
        self.assertEqual(vir_status_to_tag_colour(awaiting_la), BLUE)
        self.assertEqual(vir_status_to_tag_colour(closed), GREEN)

    def test_returns_default_tag_colour_for_unknown_status(self):
        self.assertEqual(
            vir_status_to_tag_colour("Not a real label"),
            no_vir_status.tag_colour,
        )

    def test_returns_default_tag_colour_for_none(self):
        self.assertEqual(vir_status_to_tag_colour(None), no_vir_status.tag_colour)


class GetCheckTypeLabelTests(BaseSimpleTestCase):
    def test_returns_label_for_valid_check_type(self):
        for check_type in VisaInformationRequest.RequestedCheckType:
            with self.subTest(check_type=check_type):
                self.assertEqual(
                    get_checktype_label(check_type.value), check_type.label
                )

    def test_returns_value_unchanged_for_unknown_check_type(self):
        self.assertEqual(get_checktype_label("not-a-check-type"), "not-a-check-type")

    def test_returns_none_for_none(self):
        self.assertIsNone(get_checktype_label(None))


class GetRequestTypeLabelTests(BaseSimpleTestCase):
    def test_returns_label_for_valid_request_type(self):
        for request_type in VisaInformationRequest.RequestType:
            with self.subTest(request_type=request_type):
                self.assertEqual(
                    get_requesttype_label(request_type.value), request_type.label
                )

    def test_returns_value_unchanged_for_unknown_request_type(self):
        self.assertEqual(
            get_requesttype_label("not-a-request-type"), "not-a-request-type"
        )

    def test_returns_none_for_none(self):
        self.assertIsNone(get_requesttype_label(None))
