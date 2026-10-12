"""Queries and saves for members."""

from library.models import Member


def list_members() -> list[Member]:
    return list(Member.objects.order_by("id"))


def get_member(member_id: int, for_update: bool = False) -> Member | None:
    members = Member.objects.select_for_update() if for_update else Member.objects
    return members.filter(pk=member_id).first()


def find_by_email(email: str) -> Member | None:
    """The member with exactly this email, compared as stored."""
    return Member.objects.filter(email=email).first()


def add_member(**fields) -> Member:
    return Member.objects.create(**fields)


def save_member(member: Member) -> None:
    member.save()
