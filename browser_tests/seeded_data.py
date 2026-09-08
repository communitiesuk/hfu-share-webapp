from dataclasses import dataclass


@dataclass(frozen=True)
class SeededGuest:
    id: str
    full_name: str
    first_name: str
    last_name: str
    date_of_birth: str
    email: str
    phone: str
    passport_id: str
    accommodation_request_title: str


@dataclass(frozen=True)
class SeededAccommodationRequest:
    id: str
    full_name: str
    accommodation_request_title: str
    address: str
    sponsor: str


GUEST_CONFIRMED_VISA_CHECKS_REQUIRED = SeededGuest(
    id="browser-test-person-00027",
    full_name="Ian Yates",
    first_name="Ian",
    last_name="Yates",
    date_of_birth="12 June 1966",
    email="cliffordgreen@example.org",
    phone="01214960497",
    passport_id="36DSA4XOW",
    accommodation_request_title="Ian Yates and 1 other to Flat 32J Bates, SW0Y 7AR",
)
GUEST_ARRIVED_VISA_CHECKS_REQUIRED = SeededGuest(
    id="browser-test-person-00032",
    full_name="Martyn Field",
    first_name="Martyn",
    last_name="Field",
    date_of_birth="22 January 2004",
    email="eileenstanley@example.org",
    phone="(0306)9990909",
    passport_id="B53RZIT9A",
    accommodation_request_title="Martyn Field and 1 other to 79 Owen stream, N4J 5SJ",
)

AR_CHECKS_REQUIRED_THREE_GUESTS = SeededAccommodationRequest(
    id="browser-test-ar-00030",
    full_name="Helen Walker and 2 others",
    accommodation_request_title="Helen Walker and 2 others to 6 Luke avenue,, L1 6XL",
    address="6 Luke avenue, Hobbiton",
    sponsor="Colin Khan (alice57@example.org)",
)
AR_CHECKS_REQUIRED_TWO_GUESTS = SeededAccommodationRequest(
    id="browser-test-ar-00005",
    full_name="Kirsty Hawkins and 1 other",
    accommodation_request_title=(
        "Kirsty Hawkins and 1 other to Studio 83 Evan, TF57 2UR"
    ),
    address="Studio 83 Evans canyon, Hobbiton",
    sponsor="Michael Murphy (hughesjohn@example.org)",
)
AR_REJECTED_OUTBOUND_REASSIGNMENT = SeededAccommodationRequest(
    id="browser-test-ar-00039",
    full_name="Howard Johnson and 2 others",
    accommodation_request_title=(
        "Howard Johnson and 2 others to 8 Fowler trail, PO4X 3EQ"
    ),
    address="8 Fowler trail, Hobbiton",
    sponsor="Julian Baker (vwilliams@example.com)",
)
AR_CHECKS_PARTIALLY_COMPLETED_WITH_CASE_COMMENTS = SeededAccommodationRequest(
    id="browser-test-ar-00011",
    full_name="Jonathan Greenwood and 1 other",
    accommodation_request_title=(
        "Jonathan Greenwood and 1 other to 35 Amelia fiel, L8 1TQ"
    ),
    address="35 Amelia field, Hobbiton",
    sponsor="Adrian Gardner (boylemandy@example.org)",
)
AR_DEDUPLICATED_GUEST_PAIR = SeededAccommodationRequest(
    id="browser-test-ar-00042",
    full_name="Eileen Austin",
    accommodation_request_title="Eileen Austin to 76 Helen sprin, B8 3RS",
    address="76 Helen spring, Hobbiton",
    sponsor="June Evans (hporter@example.org)",
)
