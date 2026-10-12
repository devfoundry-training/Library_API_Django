"""python manage.py serve

What every start-up does: run the migrations, load the sample data if the
database is empty, then serve the API with Waitress on HOST:PORT.
"""

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from waitress import serve

from config.wsgi import application
from library.services import sample_data


class Command(BaseCommand):
    help = "Migrate, seed an empty database, and serve the API (HOST and PORT from the environment)."

    def handle(self, *args, **options):
        call_command("migrate", interactive=False, verbosity=1)
        if sample_data.load_if_empty():
            self.stdout.write("Loaded the sample data into the empty database.")
        mode = "on (POST /test/reset and X-Today work)" if settings.TEST_MODE else "off"
        self.stdout.write(f"Library API on http://{settings.HOST}:{settings.PORT}  TEST_MODE {mode}")
        serve(application, host=settings.HOST, port=settings.PORT, threads=8, ident="library-api")
