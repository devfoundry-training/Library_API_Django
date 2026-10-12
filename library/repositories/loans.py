"""Queries and saves for loans.

Loans come back with their member loaded, because the member's type decides the
due date and the fine.
"""

from datetime import date

from library.models import Book, Loan, Member


def list_loans(member_id: int | None = None, active: bool | None = None) -> list[Loan]:
    loans = Loan.objects.select_related("member")
    if member_id is not None:
        loans = loans.filter(member_id=member_id)
    if active is not None:
        loans = loans.filter(returned__isnull=active)
    return list(loans.order_by("id"))


def get_loan(loan_id: int, for_update: bool = False) -> Loan | None:
    loans = Loan.objects.select_related("member")
    if for_update:
        loans = loans.select_for_update()
    return loans.filter(pk=loan_id).first()


def count_open_loans(member_id: int) -> int:
    return Loan.objects.filter(member_id=member_id, returned__isnull=True).count()


def add_loan(book: Book, member: Member, borrowed: date) -> Loan:
    return Loan.objects.create(book=book, member=member, borrowed=borrowed, returned=None)


def save_loan(loan: Loan) -> None:
    loan.save()
