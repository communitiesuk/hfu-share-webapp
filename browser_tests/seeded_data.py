from dataclasses import dataclass

# Shapes for describing a record the browser test seeder creates, so a browser
# test can declare the seeded records it relies on. Instances live in the test
# module that uses them, with the record's seeded id; the seeder unit test
# test_browser_test_seeded_records looks each one up by id and checks the values.
# To rely on a record type not described here, add a dataclass with the id and
# the fields the test asserts on screen, and extend that unit test to check it.


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
    guest_full_names: tuple[str, ...] = ()
