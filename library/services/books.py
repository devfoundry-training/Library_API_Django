"""Books: search, availability, and the rules for changing and deleting."""

from dataclasses import asdict

from library.repositories import books as book_repo
from library.repositories.transactions import atomic

from .errors import BookHasLoans, BookNotFound, CopiesBelowOnLoan
from .records import BookData, BookRecord
from .validation import check_book


def available(copies: int, on_loan: int) -> int:
    """Copies the library owns minus the copies on loan."""
    return copies - on_loan


def to_record(book) -> BookRecord:
    return BookRecord(id=book.id, title=book.title, author=book.author, year=book.year, genre=book.genre,
                      copies=book.copies, format=book.format, length=book.length,
                      available=available(book.copies, book.on_loan))


def list_books(title: str | None = None, author: str | None = None, genre: str | None = None) -> list[BookRecord]:
    """title and author match anywhere ignoring case, genre matches whole ignoring case, AND together."""
    return [to_record(book) for book in book_repo.list_books(title=title, author=author, genre=genre)]


def get_book(book_id: int) -> BookRecord:
    book = book_repo.get_book(book_id)
    if book is None:
        raise BookNotFound(book_id)
    return to_record(book)


def create_book(data: BookData) -> BookRecord:
    check_book(data)
    return to_record(book_repo.add_book(**asdict(data)))


def update_book(book_id: int, data: BookData) -> BookRecord:
    """Replace every field. copies may not go below the copies on loan."""
    check_book(data)
    with atomic():
        book = book_repo.get_book(book_id, for_update=True)
        if book is None:
            raise BookNotFound(book_id)
        if data.copies < book.on_loan:
            raise CopiesBelowOnLoan(book.on_loan)
        for field, value in asdict(data).items():
            setattr(book, field, value)
        book_repo.save_book(book)
        return to_record(book)


def delete_book(book_id: int) -> None:
    """Only a book that has never been lent can go, so the loan history stays complete."""
    with atomic():
        book = book_repo.get_book(book_id, for_update=True)
        if book is None:
            raise BookNotFound(book_id)
        if book_repo.has_loans(book_id):
            raise BookHasLoans(book.title)
        book_repo.delete_book(book)
