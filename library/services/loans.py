"""Loans: borrowing (the task 07 order of checks), returning, due dates, overdue and fines."""

from datetime import date

from library.repositories import books as book_repo
from library.repositories import loans as loan_repo
from library.repositories import members as member_repo
from library.repositories.transactions import atomic

from . import policies
from .books import available
from .errors import (AlreadyReturned, BookNotFound, LoanLimitReached, LoanNotFound, MemberNotFound,
                     NoCopiesAvailable, ReturnBeforeBorrowed)
from .records import LoanRecord


def to_record(loan, today: date) -> LoanRecord:
    """Work out due, overdue, days late and fine from the member's current type and today."""
    member_type = loan.member.type
    due = policies.due_date(loan.borrowed, member_type)
    late = policies.days_late(due, loan.returned, today)
    return LoanRecord(id=loan.id, book_id=loan.book_id, member_id=loan.member_id, borrowed=loan.borrowed,
                      due=due, returned=loan.returned, overdue=policies.is_overdue(due, loan.returned, today),
                      days_late=late, fine=policies.fine(late, member_type))


def list_loans(today: date, member_id: int | None = None, active: bool | None = None,
               overdue: bool | None = None) -> list[LoanRecord]:
    """Filters combine with AND. An unknown member_id is a filter, so it gives []."""
    records = [to_record(loan, today) for loan in loan_repo.list_loans(member_id=member_id, active=active)]
    if overdue is not None:
        records = [record for record in records if record.overdue == overdue]
    return records


def get_loan(loan_id: int, today: date) -> LoanRecord:
    loan = loan_repo.get_loan(loan_id)
    if loan is None:
        raise LoanNotFound(loan_id)
    return to_record(loan, today)


def borrow(member_id: int, book_id: int, today: date) -> LoanRecord:
    """The checks run in this order and the first failure decides the answer:
    the member exists, the book exists, the member is under the limit, a copy is available."""
    with atomic():
        member = member_repo.get_member(member_id, for_update=True)
        if member is None:
            raise MemberNotFound(member_id)
        book = book_repo.get_book(book_id, for_update=True)
        if book is None:
            raise BookNotFound(book_id)
        open_loans = loan_repo.count_open_loans(member_id)
        limit = policies.policy_for(member.type).max_loans
        if open_loans >= limit:
            raise LoanLimitReached(member.name, open_loans, limit)
        if available(book.copies, book.on_loan) <= 0:
            raise NoCopiesAvailable(book.title)
        return to_record(loan_repo.add_loan(book, member, borrowed=today), today)


def return_loan(loan_id: int, today: date) -> LoanRecord:
    """Sets returned to today. The loan keeps the fine from its return date."""
    with atomic():
        loan = loan_repo.get_loan(loan_id, for_update=True)
        if loan is None:
            raise LoanNotFound(loan_id)
        if loan.returned is not None:
            raise AlreadyReturned(loan_id)
        if today < loan.borrowed:
            raise ReturnBeforeBorrowed(loan_id, loan.borrowed, today)
        loan.returned = today
        loan_repo.save_loan(loan)
        return to_record(loan, today)
