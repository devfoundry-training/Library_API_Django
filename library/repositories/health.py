"""A cheap query that proves the database answers."""

from django.db import connection


def ping() -> None:
    """Raise if the database cannot be reached."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
