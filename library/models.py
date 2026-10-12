"""The three tables from the contract's db/schema.sql as Django models.

Only stored facts live here. available, due, days_late, fine and overdue are
worked out by the service layer every time, so they are not columns.
"""

from django.db import models
from django.db.models import F, Q


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    year = models.IntegerField()
    genre = models.CharField(max_length=50)
    copies = models.IntegerField()
    format = models.CharField(max_length=10)
    length = models.IntegerField()

    class Meta:
        db_table = "books"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=Q(year__gte=1450, year__lte=2100), name="books_year_range"),
            models.CheckConstraint(condition=Q(copies__gte=0), name="books_copies_not_negative"),
            models.CheckConstraint(condition=Q(format__in=["print", "ebook", "audio"]), name="books_format_known"),
            models.CheckConstraint(condition=Q(length__gt=0), name="books_length_positive"),
        ]

    def __str__(self):
        return self.title


class Member(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10)
    joined = models.DateField()

    class Meta:
        db_table = "members"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=Q(type__in=["standard", "student", "staff"]), name="members_type_known"),
        ]

    def __str__(self):
        return self.name


class Loan(models.Model):
    # PROTECT: a book or member with loans is never removed underneath them.
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="loans", db_column="book_id")
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="loans", db_column="member_id")
    borrowed = models.DateField()
    returned = models.DateField(null=True)

    class Meta:
        db_table = "loans"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(returned__isnull=True) | Q(returned__gte=F("borrowed")),
                name="loans_returned_not_before_borrowed",
            ),
        ]
