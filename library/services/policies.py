"""Loan policies (task 06) and the date arithmetic built on them (task 09).

Due date, days late and fine are always worked out from the member's current
type and today. Nothing here reads the clock.
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class LoanPolicy:
    loan_days: int
    fine_per_day: int  # pence
    max_loans: int


POLICIES = {
    "standard": LoanPolicy(loan_days=14, fine_per_day=25, max_loans=3),
    "student": LoanPolicy(loan_days=21, fine_per_day=10, max_loans=5),
    "staff": LoanPolicy(loan_days=28, fine_per_day=0, max_loans=10),
}

MEMBER_TYPES = tuple(POLICIES)


def policy_for(member_type: str) -> LoanPolicy:
    return POLICIES[member_type]


def due_date(borrowed: date, member_type: str) -> date:
    return borrowed + timedelta(days=policy_for(member_type).loan_days)


def is_overdue(due: date, returned: date | None, today: date) -> bool:
    """Open and past the due date. Due today is not overdue."""
    return returned is None and today > due


def days_late(due: date, returned: date | None, today: date) -> int:
    """Returned loans count to the return date, open loans to today. Never below 0."""
    end = returned if returned is not None else today
    return max((end - due).days, 0)


def fine(days: int, member_type: str) -> int:
    """Whole pence, no cap."""
    return days * policy_for(member_type).fine_per_day
