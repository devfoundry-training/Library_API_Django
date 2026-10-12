"""python manage.py seed_library [--reset]

Loads the sample data into an empty database. --reset empties the tables first,
the same as POST /test/reset.
"""

from django.core.management.base import BaseCommand

from library.services import sample_data


class Command(BaseCommand):
    help = "Load the sample books, members and loans (only into an empty database unless --reset)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="empty the tables first")

    def handle(self, *args, **options):
        if options["reset"]:
            sample_data.reset()
            self.stdout.write("Sample data reset: 20 books, 9 members, 12 loans.")
        elif sample_data.load_if_empty():
            self.stdout.write("Sample data loaded: 20 books, 9 members, 12 loans.")
        else:
            self.stdout.write("The database already has data: nothing loaded.")
