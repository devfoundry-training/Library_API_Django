"""Books: availability, search, and the rules for changing and deleting."""

from dataclasses import replace

from library.services import books
from library.services import errors as e
from library.services.records import BookData

from .base import ServiceTestCase

DUNE = BookData(title="Dune", author="Frank Herbert", year=1965, genre="Science Fiction", copies=4,
                format="print", length=412)


class Books(ServiceTestCase):

    def test_available_is_copies_minus_open_loans(self):
        found = {book.id: book.available for book in books.list_books()}
        self.assertEqual((found[4], found[1], found[5], found[3]), (3, 2, 0, 0))

    def test_search(self):
        def ids(**filters):
            return [book.id for book in books.list_books(**filters)]
        self.assertEqual(ids(title="the"), [3, 6, 9, 10, 11, 14, 17, 20])
        self.assertEqual(ids(author="orwell"), [2, 7])
        self.assertEqual(ids(genre="science fiction"), [4, 6, 9, 14, 20])
        self.assertEqual(ids(genre="science"), [])
        self.assertEqual(ids(author="wells", genre="Science Fiction"), [6, 20])

    def test_create_gets_the_next_id(self):
        book = books.create_book(replace(DUNE, title="Piranesi"))
        self.assertEqual((book.id, book.available), (21, 4))

    def test_create_refuses_invalid_values(self):
        with self.assertRaises(e.InvalidInput):
            books.create_book(replace(DUNE, year=3000))
        self.assertEqual(len(books.list_books()), 20)

    def test_copies_cannot_go_below_copies_on_loan(self):
        with self.assertRaisesMessage(e.CopiesBelowOnLoan, "copies cannot be less than the 1 on loan"):
            books.update_book(4, replace(DUNE, copies=0))
        updated = books.update_book(4, replace(DUNE, copies=1))
        self.assertEqual((updated.copies, updated.available), (1, 0))

    def test_update_unknown_book(self):
        with self.assertRaisesMessage(e.BookNotFound, "no book with id 99"):
            books.update_book(99, DUNE)

    def test_book_with_loans_cannot_be_deleted(self):
        with self.assertRaisesMessage(e.BookHasLoans, "Pride and Prejudice has loans and cannot be deleted"):
            books.delete_book(1)
        # only a returned loan: the history still counts
        with self.assertRaises(e.BookHasLoans):
            books.delete_book(13)

    def test_book_without_loans_is_deleted(self):
        books.delete_book(8)
        with self.assertRaises(e.BookNotFound):
            books.get_book(8)
