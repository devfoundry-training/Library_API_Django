"""Members: unique emails, joined defaults to today, and a member's loans."""

from datetime import date

from library.repositories import members as member_repo
from library.repositories.transactions import atomic

from . import loans as loan_service
from .errors import EmailTaken, MemberNotFound
from .records import LoanRecord, MemberData, MemberRecord
from .validation import check_member


def to_record(member) -> MemberRecord:
    return MemberRecord(id=member.id, name=member.name, email=member.email, type=member.type,
                        joined=member.joined)


def list_members() -> list[MemberRecord]:
    return [to_record(member) for member in member_repo.list_members()]


def get_member(member_id: int) -> MemberRecord:
    member = member_repo.get_member(member_id)
    if member is None:
        raise MemberNotFound(member_id)
    return to_record(member)


def _check_email_free(email: str, member_id: int | None = None) -> None:
    """Emails are compared exactly as stored. Keeping your own email is fine."""
    owner = member_repo.find_by_email(email)
    if owner is not None and owner.id != member_id:
        raise EmailTaken(email, owner.id)


def create_member(data: MemberData, today: date) -> MemberRecord:
    check_member(data)
    with atomic():
        _check_email_free(data.email)
        member = member_repo.add_member(name=data.name, email=data.email, type=data.type,
                                        joined=data.joined or today)
        return to_record(member)


def update_member(member_id: int, data: MemberData) -> MemberRecord:
    """Replace every field. A type change moves the due dates of open loans with it."""
    check_member(data)
    with atomic():
        member = member_repo.get_member(member_id, for_update=True)
        if member is None:
            raise MemberNotFound(member_id)
        _check_email_free(data.email, member_id)
        member.name, member.email, member.type, member.joined = data.name, data.email, data.type, data.joined
        member_repo.save_member(member)
        return to_record(member)


def list_member_loans(member_id: int, today: date, active: bool | None = None,
                      overdue: bool | None = None) -> list[LoanRecord]:
    if member_repo.get_member(member_id) is None:
        raise MemberNotFound(member_id)
    return loan_service.list_loans(today, member_id=member_id, active=active, overdue=overdue)
