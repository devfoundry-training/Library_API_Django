"""The value rules from RULES.md, Validation: no database."""

from dataclasses import replace
from datetime import date

from django.test import SimpleTestCase

from library.services.errors import InvalidInput
from library.services.records import BookData, MemberData
from library.services.validation import check_book, check_member

BOOK = BookData(title="Piranesi", author="Susanna Clarke", year=2020, genre="Fantasy", copies=2,
                format="print", length=272)
MEMBER = MemberData(name="Iris Murdoch", email="iris.murdoch@example.com", type="student",
                    joined=date(2026, 10, 1))


class BookRules(SimpleTestCase):

    def test_a_valid_book_and_the_boundaries_pass(self):
        check_book(BOOK)
        check_book(replace(BOOK, year=1450, copies=0, length=1))
        check_book(replace(BOOK, year=2100, title="T" * 100, author="A" * 100, genre="G" * 50))

    def test_rule_violations_are_invalid_input(self):
        cases = {
            "blank title": (replace(BOOK, title="   "), "title must not be blank"),
            "empty genre": (replace(BOOK, genre=""), "genre must not be blank"),
            "title too long": (replace(BOOK, title="T" * 101), "title must be at most 100 characters"),
            "year 1449": (replace(BOOK, year=1449), "year must be between 1450 and 2100"),
            "year 2101": (replace(BOOK, year=2101), "year must be between 1450 and 2100"),
            "negative copies": (replace(BOOK, copies=-1), "copies must not be negative"),
            "unknown format": (replace(BOOK, format="tablet"), "format must be print, ebook or audio, got 'tablet'"),
            "length 0": (replace(BOOK, length=0), "length must be positive"),
        }
        for name, (data, message) in cases.items():
            with self.subTest(name):
                with self.assertRaisesMessage(InvalidInput, message):
                    check_book(data)


class MemberRules(SimpleTestCase):

    def test_a_valid_member_passes(self):
        check_member(MEMBER)

    def test_rule_violations_are_invalid_input(self):
        cases = {
            "blank name": replace(MEMBER, name=" "),
            "email without @": replace(MEMBER, email="not-an-email"),
            "email with a space": replace(MEMBER, email="iris murdoch@example.com"),
            "email with two @": replace(MEMBER, email="a@b@example.com"),
            "unknown type": replace(MEMBER, type="visitor"),
        }
        for name, data in cases.items():
            with self.subTest(name):
                with self.assertRaises(InvalidInput):
                    check_member(data)
