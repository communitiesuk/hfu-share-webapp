from dataclasses import dataclass


@dataclass(frozen=True)
class SeededGuest:
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
    full_name: str
    accommodation_request_title: str
    address: str
    sponsor: str
