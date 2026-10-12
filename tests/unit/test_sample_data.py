"""The reset puts the sample data back, and the id counters with it."""

from library.services import books, loans, members, sample_data
from library.services.records import MemberData

from .base import TODAY, ServiceTestCase


class SampleData(ServiceTestCase):

    def test_reset_restores_rows_and_next_ids(self):
        books.delete_book(8)
        loans.borrow(101, 4, TODAY)
        members.create_member(MemberData("Iris Murdoch", "iris@example.com", "student"), TODAY)
        sample_data.reset()
        counts = (len(books.list_books()), len(members.list_members()), len(loans.list_loans(TODAY)))
        self.assertEqual(counts, (20, 9, 12))
        self.assertEqual(loans.borrow(101, 4, TODAY).id, 13)
        self.assertEqual(members.create_member(MemberData("Iris", "i@example.com", "staff"), TODAY).id, 110)

    def test_load_if_empty_leaves_existing_data_alone(self):
        self.assertFalse(sample_data.load_if_empty())
