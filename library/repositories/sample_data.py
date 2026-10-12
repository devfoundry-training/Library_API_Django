"""Loading the sample data (library/sample_data/seed.sql) and resetting the id counters.

seed.sql is a copy of db/seed.sql from the contract repository. It has no
semicolons inside comments or strings, so it can be split on semicolons.
"""

from pathlib import Path

from django.db import connection, transaction

from library.models import Book, Loan, Member

SEED_FILE = Path(__file__).resolve().parent.parent / "sample_data" / "seed.sql"
TABLES = ("loans", "members", "books")


def _seed_statements() -> list[str]:
    lines = [line for line in SEED_FILE.read_text(encoding="utf-8").splitlines()
             if not line.lstrip().startswith("--")]
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


def is_empty() -> bool:
    return not (Book.objects.exists() or Member.objects.exists() or Loan.objects.exists())


def load(clear: bool) -> None:
    """Insert the sample rows, emptying the tables first when `clear` is true.

    One transaction, so a request never sees half the data.
    """
    vendor = connection.vendor
    with transaction.atomic(), connection.cursor() as cursor:
        if clear:
            if vendor == "postgresql":
                # Django's foreign keys are DEFERRABLE INITIALLY DEFERRED. Check them now,
                # because TRUNCATE refuses to run while deferred checks are pending
                # (after earlier writes in the same transaction, as in a unit test).
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                cursor.execute("TRUNCATE loans, members, books RESTART IDENTITY")
            else:
                for table in TABLES:
                    cursor.execute(f"DELETE FROM {table}")
        if vendor == "sqlite":
            # Django declares SQLite ids AUTOINCREMENT, which keeps its own counter
            # in sqlite_sequence. Clearing it makes the next ids follow the seed.
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('loans', 'members', 'books')")
        for statement in _seed_statements():
            cursor.execute(statement)
        if vendor == "postgresql":
            # Explicit ids never move an identity sequence: move each one past the highest id.
            for table in reversed(TABLES):
                cursor.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE(MAX(id), 0) + 1, false) FROM {table}"
                )
