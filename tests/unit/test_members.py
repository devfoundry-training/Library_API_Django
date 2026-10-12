"""Members: unique emails, joined defaults to today, type changes move due dates."""

from datetime import date

from library.services import errors as e
from library.services import loans, members
from library.services.records import MemberData

from .base import TODAY, ServiceTestCase

IRIS = MemberData(name="Iris Murdoch", email="iris.murdoch@example.com", type="student")


class Members(ServiceTestCase):

    def test_create_gets_the_next_id_and_joined_defaults_to_today(self):
        member = members.create_member(IRIS, TODAY)
        self.assertEqual((member.id, member.joined), (110, TODAY))

    def test_duplicate_email_on_create(self):
        taken = MemberData(name="Someone", email="amira.khan@example.com", type="standard")
        with self.assertRaisesMessage(e.EmailTaken, "email amira.khan@example.com is already used by member 101"):
            members.create_member(taken, TODAY)

    def test_duplicate_email_on_update_but_own_email_is_fine(self):
        ben = members.get_member(102)
        with self.assertRaisesMessage(e.EmailTaken, "email ella.brown@example.com is already used by member 105"):
            members.update_member(102, MemberData(ben.name, "ella.brown@example.com", ben.type, ben.joined))
        updated = members.update_member(102, MemberData("Ben Taylor-Smith", ben.email, "staff", date(2024, 9, 3)))
        self.assertEqual((updated.name, updated.type), ("Ben Taylor-Smith", "staff"))

    def test_update_unknown_member(self):
        with self.assertRaisesMessage(e.MemberNotFound, "no member with id 999"):
            members.update_member(999, MemberData("X", "x@example.com", "standard", TODAY))

    def test_type_change_moves_due_dates(self):
        self.assertEqual(loans.get_loan(5, TODAY).due, date(2026, 10, 15))
        amira = members.get_member(101)
        members.update_member(101, MemberData(amira.name, amira.email, "staff", amira.joined))
        self.assertEqual(loans.get_loan(5, TODAY).due, date(2026, 10, 29))

    def test_member_loans(self):
        self.assertEqual([loan.id for loan in members.list_member_loans(105, TODAY)], [4, 11])
        self.assertEqual([loan.id for loan in members.list_member_loans(102, TODAY, active=False)], [2])
        with self.assertRaises(e.MemberNotFound):
            members.list_member_loans(999, TODAY)
