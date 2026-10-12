"""The value rules from RULES.md, Validation. Every failure is InvalidInput (400).

The API layer has already checked the JSON types (text is text, whole numbers are
whole numbers, dates are real dates). These checks are about the values.
"""

import re

from .errors import InvalidInput
from .policies import MEMBER_TYPES
from .records import BookData, MemberData

BOOK_FORMATS = ("print", "ebook", "audio")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+")


def _text(field: str, value: str, max_length: int) -> None:
    if not value.strip():
        raise InvalidInput(f"{field} must not be blank")
    if len(value) > max_length:
        raise InvalidInput(f"{field} must be at most {max_length} characters")


def check_book(data: BookData) -> None:
    _text("title", data.title, 100)
    _text("author", data.author, 100)
    if not 1450 <= data.year <= 2100:
        raise InvalidInput("year must be between 1450 and 2100")
    _text("genre", data.genre, 50)
    if data.copies < 0:
        raise InvalidInput("copies must not be negative")
    if data.format not in BOOK_FORMATS:
        raise InvalidInput(f"format must be print, ebook or audio, got '{data.format}'")
    if data.length <= 0:
        raise InvalidInput("length must be positive")


def check_member(data: MemberData) -> None:
    _text("name", data.name, 100)
    if len(data.email) > 100 or not EMAIL_PATTERN.fullmatch(data.email):
        raise InvalidInput("email must look like name@example.com")
    if data.type not in MEMBER_TYPES:
        raise InvalidInput("member type must be standard, student or staff")
