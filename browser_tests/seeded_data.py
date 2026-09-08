from dataclasses import dataclass

# Records the browser tests expect to find in the seeded browser test local
# authority. Each test module declares the records it uses; the seeder unit test
# test_browser_test_seeded_records checks they exist with these values, so a
# change to the seeder fails in CI rather than as a failing browser test on dev.
# A record that a test modifies (merging, adding checks) should belong to that
# test alone, since the whole suite runs against one seed.


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
