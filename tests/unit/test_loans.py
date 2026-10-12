"""Borrowing and returning through the loan service, with today passed in."""

from datetime import date

from library.services import books, loans
from library.services import errors as e

from .base import TODAY, ServiceTestCase


class Borrowing(ServiceTestCase):

    def test_borrow_reduces_available(self):
        loan = loans.borrow(101, 4, TODAY)
        self.assertEqual((loan.id, loan.borrowed, loan.due, loan.returned), (13, TODAY, date(2026, 10, 26), None))
        self.assertEqual(books.get_book(4).available, 2)

    def test_return_restores_available(self):
        loans.return_loan(4, TODAY)
        self.assertEqual(books.get_book(5).available, 1)

    def test_unknown_member(self):
        with self.assertRaisesMessage(e.MemberNotFound, "no member with id 999"):
            loans.borrow(999, 1, TODAY)

    def test_unknown_book(self):
        with self.assertRaisesMessage(e.BookNotFound, "no book with id 99"):
            loans.borrow(101, 99, TODAY)

    def test_member_is_checked_before_book(self):
        with self.assertRaises(e.MemberNotFound):
            loans.borrow(999, 99, TODAY)

    def test_no_copies(self):
        with self.assertRaisesMessage(e.NoCopiesAvailable, "The Hobbit has no copies available"):
            loans.borrow(101, 3, TODAY)

    def test_standard_limit_is_3(self):
        loans.borrow(105, 2, TODAY)
        with self.assertRaisesMessage(e.LoanLimitReached, "Ella Brown already has 3 loans (limit 3)"):
            loans.borrow(105, 7, TODAY)

    def test_student_limit_is_5(self):
        for book_id in (1, 2, 4, 6):
            loans.borrow(102, book_id, TODAY)
        with self.assertRaisesMessage(e.LoanLimitReached, "Ben Taylor already has 5 loans (limit 5)"):
            loans.borrow(102, 7, TODAY)

    def test_limit_is_checked_before_copies(self):
        loans.borrow(105, 2, TODAY)
        with self.assertRaises(e.LoanLimitReached):
            loans.borrow(105, 3, TODAY)

    def test_refused_borrow_adds_no_loan(self):
        with self.assertRaises(e.NoCopiesAvailable):
            loans.borrow(101, 3, TODAY)
        self.assertEqual([loan.id for loan in loans.list_loans(TODAY)], list(range(1, 13)))


class DatesAndFines(ServiceTestCase):

    def test_sample_loans_on_2026_10_12(self):
        # loan id: (due, days late, fine, overdue), the last table in RULES.md
        expected = {
            1: (date(2026, 9, 15), 0, 0, False), 2: (date(2026, 10, 1), 4, 40, False),
            3: (date(2026, 10, 3), 9, 0, True), 4: (date(2026, 10, 4), 8, 200, True),
            5: (date(2026, 10, 15), 0, 0, False), 6: (date(2026, 9, 18), 24, 240, True),
            7: (date(2026, 10, 24), 0, 0, False), 8: (date(2026, 10, 6), 6, 60, True),
            9: (date(2026, 8, 29), 12, 0, False), 10: (date(2026, 10, 12), 0, 0, False),
            11: (date(2026, 10, 11), 1, 25, True), 12: (date(2026, 9, 28), 2, 50, False),
        }
        found = {loan.id: (loan.due, loan.days_late, loan.fine, loan.overdue) for loan in loans.list_loans(TODAY)}
        self.assertEqual(found, expected)

    def test_due_today_is_not_overdue_but_the_next_day_is(self):
        self.assertFalse(loans.get_loan(10, TODAY).overdue)
        later = loans.get_loan(10, date(2026, 10, 13))
        self.assertEqual((later.overdue, later.days_late, later.fine), (True, 1, 10))

    def test_staff_are_never_fined(self):
        loan = loans.get_loan(3, date(2027, 1, 1))
        self.assertEqual((loan.days_late, loan.fine), (90, 0))

    def test_returned_loan_keeps_the_fine_from_its_return_date(self):
        self.assertEqual(loans.get_loan(2, date(2027, 1, 1)).fine, 40)

    def test_filters(self):
        def ids(**filters):
            return [loan.id for loan in loans.list_loans(TODAY, **filters)]
        self.assertEqual(ids(overdue=True), [3, 4, 6, 8, 11])
        self.assertEqual(ids(active=True, overdue=False), [5, 7, 10])
        self.assertEqual(ids(member_id=102, active=True), [8])
        self.assertEqual(ids(member_id=999), [])


class Returning(ServiceTestCase):

    def test_return_sets_returned_and_the_final_fine(self):
        loan = loans.return_loan(4, TODAY)
        self.assertEqual((loan.returned, loan.overdue, loan.days_late, loan.fine), (TODAY, False, 8, 200))

    def test_already_returned(self):
        with self.assertRaisesMessage(e.AlreadyReturned, "loan 1 has already been returned"):
            loans.return_loan(1, TODAY)

    def test_return_before_borrowed(self):
        message = "loan 7 was borrowed on 2026-10-10 and cannot be returned on 2026-10-01"
        with self.assertRaisesMessage(e.ReturnBeforeBorrowed, message):
            loans.return_loan(7, date(2026, 10, 1))
        self.assertIsNone(loans.get_loan(7, TODAY).returned)

    def test_unknown_loan(self):
        with self.assertRaisesMessage(e.LoanNotFound, "no loan with id 99"):
            loans.return_loan(99, TODAY)

    def test_returning_frees_a_place_under_the_limit(self):
        loans.borrow(105, 2, TODAY)
        with self.assertRaises(e.LoanLimitReached):
            loans.borrow(105, 7, TODAY)
        loans.return_loan(4, TODAY)
        self.assertEqual(loans.borrow(105, 7, TODAY).member_id, 105)
