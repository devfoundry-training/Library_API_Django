"""Loan policies and date arithmetic: pure functions, no database."""

from datetime import date

from django.test import SimpleTestCase

from library.services import policies


class DueDates(SimpleTestCase):

    def test_due_date_per_member_type(self):
        borrowed = date(2026, 10, 12)
        self.assertEqual(policies.due_date(borrowed, "standard"), date(2026, 10, 26))
        self.assertEqual(policies.due_date(borrowed, "student"), date(2026, 11, 2))
        self.assertEqual(policies.due_date(borrowed, "staff"), date(2026, 11, 9))

    def test_due_date_crosses_the_year_end(self):
        self.assertEqual(policies.due_date(date(2026, 12, 20), "student"), date(2027, 1, 10))

    def test_due_date_in_a_leap_year(self):
        self.assertEqual(policies.due_date(date(2028, 2, 20), "standard"), date(2028, 3, 5))


class OverdueAndFines(SimpleTestCase):

    def test_due_today_is_not_overdue(self):
        due = date(2026, 10, 12)
        self.assertFalse(policies.is_overdue(due, None, date(2026, 10, 12)))
        self.assertEqual(policies.days_late(due, None, date(2026, 10, 12)), 0)
        self.assertTrue(policies.is_overdue(due, None, date(2026, 10, 13)))

    def test_a_returned_loan_is_never_overdue(self):
        self.assertFalse(policies.is_overdue(date(2026, 10, 1), date(2026, 10, 5), date(2026, 10, 12)))

    def test_days_late_is_never_below_zero(self):
        self.assertEqual(policies.days_late(date(2026, 10, 15), None, date(2026, 10, 12)), 0)

    def test_one_day_late_standard_is_25(self):
        self.assertEqual(policies.fine(1, "standard"), 25)

    def test_ten_days_late_student_is_100(self):
        self.assertEqual(policies.fine(10, "student"), 100)

    def test_staff_are_never_fined(self):
        self.assertEqual(policies.fine(90, "staff"), 0)

    def test_returned_loan_counts_days_to_the_return_date(self):
        self.assertEqual(policies.days_late(date(2026, 10, 1), date(2026, 10, 5), date(2027, 1, 1)), 4)

    def test_loan_limits(self):
        self.assertEqual([policies.policy_for(t).max_loans for t in ("standard", "student", "staff")], [3, 5, 10])
