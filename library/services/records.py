"""Plain data going into and out of the services.

The API layer builds the *Data objects from a validated request and renders the
*Record objects as JSON. No ORM model crosses the service boundary upwards.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BookData:
    title: str
    author: str
    year: int
    genre: str
    copies: int
    format: str
    length: int


@dataclass(frozen=True)
class MemberData:
    name: str
    email: str
    type: str
    joined: date | None = None  # only a new member may leave it out


@dataclass(frozen=True)
class BookRecord:
    id: int
    title: str
    author: str
    year: int
    genre: str
    copies: int
    format: str
    length: int
    available: int


@dataclass(frozen=True)
class MemberRecord:
    id: int
    name: str
    email: str
    type: str
    joined: date


@dataclass(frozen=True)
class LoanRecord:
    id: int
    book_id: int
    member_id: int
    borrowed: date
    due: date
    returned: date | None
    overdue: bool
    days_late: int
    fine: int
