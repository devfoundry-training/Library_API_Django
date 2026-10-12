"""Shared set-up: the sample data in a test database, and the fixed date from RULES.md."""

from datetime import date

from django.test import TestCase

from library.services import sample_data

TODAY = date(2026, 10, 12)


class ServiceTestCase(TestCase):
    """Loads the sample data once per class. Django rolls back each test's changes."""

    @classmethod
    def setUpTestData(cls):
        sample_data.reset()
