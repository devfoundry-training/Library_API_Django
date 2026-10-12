"""Queries and saves for books.

Each book comes back with an `on_loan` count (its loans with no returned date),
which the service layer turns into `available`.
"""

from django.db.models import Count, Q, QuerySet

from library.models import Book, Loan


def _with_on_loan() -> QuerySet[Book]:
    return Book.objects.annotate(on_loan=Count("loans", filter=Q(loans__returned__isnull=True)))


def list_books(title: str | None = None, author: str | None = None, genre: str | None = None) -> list[Book]:
    books = _with_on_loan()
    if title:
        books = books.filter(title__icontains=title)
    if author:
        books = books.filter(author__icontains=author)
    if genre:
        books = books.filter(genre__iexact=genre)
    return list(books.order_by("id"))


def get_book(book_id: int, for_update: bool = False) -> Book | None:
    if for_update:
        # Lock the row first (PostgreSQL), then read the count in a second query:
        # FOR UPDATE cannot be combined with an aggregate.
        if not Book.objects.select_for_update().filter(pk=book_id).exists():
            return None
    return _with_on_loan().filter(pk=book_id).first()


def add_book(**fields) -> Book:
    book = Book.objects.create(**fields)
    book.on_loan = 0
    return book


def save_book(book: Book) -> None:
    book.save()


def has_loans(book_id: int) -> bool:
    return Loan.objects.filter(book_id=book_id).exists()


def delete_book(book: Book) -> None:
    book.delete()
