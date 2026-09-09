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
    guest_full_names: tuple[str, ...] = ()
