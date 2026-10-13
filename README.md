# Library API: Django

[![CI](https://github.com/devfoundry-training/Library_API_Django/actions/workflows/ci.yml/badge.svg)](https://github.com/devfoundry-training/Library_API_Django/actions/workflows/ci.yml)

The Library API built with Django 5.2 and Django REST framework, with the Django ORM and migrations, SQLite on a
laptop and PostgreSQL 17 in Docker Compose. Part of the DevFoundry Library API series: one REST API built the same
way in several stacks, all checked by the same conformance suite from
[Library_API_Contract](https://github.com/devfoundry-training/Library_API_Contract).

The domain is the library from the Zero to Hero courses: books, members, loans and fines, with the same rules as
the Zero to Hero task pack.

---

## Who Is This For?

- Developers who know some Django and want to see a layered API rather than a ModelViewSet over the tables
- Delegates on Django and DRF courses who want a realistic project with a fixed specification
- Zero to Hero learners taking the Library Manager from a console program to a web API
- Anyone comparing this repo with the FastAPI, Spring Boot and ASP.NET Core versions of the same contract

Comfort with Python, HTTP and basic SQL is assumed. No Django experience is needed to run it.

---

## Prerequisites

| Tool | Minimum Version | Needed for |
|------|-----------------|------------|
| Python | 3.13 | running the API and the tests |
| Docker with Compose | 24+ | the PostgreSQL run (optional) |
| Git | any | cloning this repo and the contract |

```bash
py -3.13 --version      # Windows
python3 --version       # macOS/Linux
```

---

## Getting Started

### Option 1: Local Run with SQLite (Recommended)

```bash
# Clone this repo, and the contract next to it (for the conformance suite)
git clone https://github.com/devfoundry-training/Library_API_Django.git
git clone https://github.com/devfoundry-training/Library_API_Contract.git
cd Library_API_Django

# Create a virtual environment
py -3.13 -m venv .venv        # Windows
python3 -m venv .venv         # macOS/Linux

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install the pinned packages
pip install -r requirements.txt

# Migrate, load the sample data into the empty database, and serve on port 8000
python manage.py serve
```

Then open http://localhost:8000/books. The database is `library.db` in the repo folder; delete it to start again.

`serve` reads its settings from the environment:

| Variable | Default | Meaning |
|----------|---------|---------|
| `PORT` | `8000` | the port the API listens on |
| `DATABASE_URL` | `sqlite:///library.db` | where the data lives, for example `postgresql://library:library@localhost:5432/library` |
| `TEST_MODE` | unset (off) | `1` turns on `POST /test/reset` and the `X-Today` header. Never set it on a real server |
| `LIBRARY_TODAY` | unset | `YYYY-MM-DD` fixes today for the whole server |
| `HOST` | `127.0.0.1` | the address to listen on (the Docker image sets `0.0.0.0`) |

To run with test mode on (needed for the conformance suite):

```bash
# Windows PowerShell
$env:TEST_MODE = "1"; python manage.py serve
# macOS/Linux
TEST_MODE=1 python manage.py serve
```

### Option 2: Docker Compose with PostgreSQL

```bash
docker compose up --build                  # the API on http://localhost:8000, data in PostgreSQL 17
TEST_MODE=1 docker compose up --build      # the same, with test mode on
docker compose down -v                     # stop and remove the database volume
```

The app container runs the migrations and loads the sample data on first start. The database port is not
published, so it never clashes with a PostgreSQL already on the machine.

> **Note:** On Windows with Docker running inside WSL, `localhost:8000` may not reach the container. Use the WSL
> distro address instead: run `wsl hostname -I` and open `http://<that address>:8000`.

---

## Repository Structure

```
config/
  settings.py              # Settings from the environment (PORT, DATABASE_URL, TEST_MODE, LIBRARY_TODAY)
  urls.py                  # Includes the API routes, JSON handlers for 400, 404 and 500
  wsgi.py
library/
  models.py                # Book, Member, Loan (db_table "books", "members", "loans", CHECK constraints)
  migrations/              # 0001_initial.py builds the schema
  api/                     # API layer
    urls.py                # Routes without trailing slashes, a 32-bit id path converter
    views.py               # APIView classes, one service call each
    serializers.py         # Strict input shapes, output shapes
    today.py               # today_for(request): X-Today, LIBRARY_TODAY, then the clock
    exceptions.py          # The one exception handler: every error as {"error": {"code", "message"}}
    negotiation.py         # Always answer JSON
  services/                # Service layer: every business rule
    books.py               # Availability, search, copies below on loan, books with loans
    members.py             # Unique email, joined defaults to today, a member's loans
    loans.py               # Borrow (order of checks), return, due, overdue, days late, fine
    policies.py            # Loan policies per member type and the date arithmetic
    validation.py          # The value rules: ranges, blank text, formats, email shape
    records.py             # Plain dataclasses in and out of the services
    errors.py              # BookNotFound, LoanLimitReached, ... with the exact messages
    sample_data.py         # Reset and load-if-empty
    health.py
  repositories/            # Repository layer: thin query and save functions over the ORM
    books.py, members.py, loans.py, sample_data.py, health.py, transactions.py
  sample_data/seed.sql     # Copy of db/seed.sql from the contract
  management/commands/
    serve.py               # Migrate, seed an empty database, serve with Waitress
    seed_library.py        # Load the sample data by hand (--reset to empty first)
tests/unit/                # Service layer tests with a fixed date, no web server
manage.py
requirements.txt           # Pinned packages
Dockerfile                 # Two stages, non-root user
docker-compose.yml         # The app and postgres:17
.github/workflows/ci.yml   # Unit tests, conformance on PostgreSQL and SQLite, image build
```

---

## Architecture

Four layers, and each one only talks to the one below it:

```
  HTTP request
       |
       v
+---------------------------+   library/api: urls, views, serializers, today_for,
|  API layer                |   the exception handler, status codes, Location headers
+---------------------------+
       |  plain values: ids, BookData / MemberData, today as a date
       v
+---------------------------+   library/services: the rules in RULES.md, the order of
|  Service layer            |   the checks, the exact 404 and 409 messages. No HTTP.
+---------------------------+
       |  ORM model instances
       v
+---------------------------+   library/repositories: queries and saves through the
|  Repository layer         |   Django ORM (counts of open loans, lookups by email)
+---------------------------+
       |
       v
+---------------------------+   SQLite or PostgreSQL, tables built by
|  Database                 |   library/migrations, CHECK rules in Meta.constraints
+---------------------------+
```

Where each rule lives:

| Rule | Where |
|------|-------|
| JSON types: whole numbers are numbers (not `"101"`, `true` or `4.5`), text is text, dates are real `YYYY-MM-DD` | `api/serializers.py` (strict fields, because DRF's own fields coerce) |
| What today is | `api/today.py`, called once per request in `LibraryView.initial` |
| Error format, status per error family | `api/exceptions.py` |
| Value rules: year 1450 to 2100, copies not negative, not blank, lengths, format, email, member type | `services/validation.py` |
| available = copies minus open loans | `services/books.py` |
| Loan policies 14/25p/3, 21/10p/5, 28/0p/10 | `services/policies.py` |
| Due date, overdue, days late, fine | `services/policies.py`, applied in `services/loans.py` |
| Borrow checks in order: member, book, limit, copies | `services/loans.py` |
| Return: already returned, not before borrowed | `services/loans.py` |
| Copies not below copies on loan, no delete for a book with loans | `services/books.py` |
| Unique email, joined defaults to today | `services/members.py` |

Some choices worth knowing about:

- **APIView, not ModelViewSet.** A viewset reads and writes the tables directly, which would put the rules in the
  serializers. Here a view parses the request, calls one service function and shapes the answer.
- **Serializers only check types.** The value rules are business rules, so they sit in the service layer where the
  unit tests reach them without HTTP.
- **Services return dataclasses** (`BookRecord`, `LoanRecord`, ...), not ORM models, so nothing above the service
  layer touches the database.
- **Services never read the clock.** Today arrives as a `date` argument, so a unit test passes `date(2026, 10, 12)`.
- **Transactions** come from `repositories/transactions.py`, so the services import no Django code at all.

---

## API

The full description is the contract's [openapi.yaml](https://github.com/devfoundry-training/Library_API_Contract/blob/main/openapi.yaml),
and the rules with worked examples are in
[RULES.md](https://github.com/devfoundry-training/Library_API_Contract/blob/main/RULES.md). In short:

| Method | Path | Success |
|--------|------|---------|
| GET | `/health` | 200 `{"status": "ok"}` |
| GET, POST | `/books` (`?title=&author=&genre=`) | 200 list, 201 + `Location` |
| GET, PUT, DELETE | `/books/{id}` | 200, 200, 204 |
| GET, POST | `/members` | 200 list, 201 + `Location` |
| GET, PUT | `/members/{id}` | 200 |
| GET | `/members/{id}/loans` (`?active=&overdue=`) | 200 list |
| GET, POST | `/loans` (`?member_id=&active=&overdue=`) | 200 list, 201 + `Location` |
| GET | `/loans/{id}` | 200 |
| POST | `/loans/{id}/return` | 200 |
| POST | `/test/reset` | 204, only with `TEST_MODE=1` |

```bash
curl http://localhost:8000/loans/11
curl -X POST http://localhost:8000/loans -H "Content-Type: application/json" -d '{"member_id": 101, "book_id": 4}'
```

---

## Running the Tests

### Unit tests (service layer)

```bash
python manage.py test tests.unit
```

51 tests with Django's test runner: the policies and date arithmetic, the value rules, borrowing, returning,
fines, changes, unique emails and the sample-data reset. They call the services directly with a fixed date and no
web server. On SQLite Django uses an in-memory database; set `DATABASE_URL` to run them on PostgreSQL.

### Conformance suite (the contract)

Start the API with test mode on (Option 1 or 2 above), then from the contract repo:

```bash
cd ../Library_API_Contract
py -3.13 conformance/run.py --base-url http://localhost:8000
```

```
Library API conformance suite against http://localhost:8000
PASS  general.test_health_returns_ok
...
60 passed, 0 failed, 60 tests in 4.8s
```

CI runs both on every push and pull request: the unit tests, then the unit tests and the conformance suite once on
PostgreSQL (a service container) and once on SQLite, then a Docker image build.

---

## Docker

- `Dockerfile` has two stages: the first installs the pinned packages into a virtual environment, the second copies
  it into a clean `python:3.13-slim` with the code and runs as the non-root user `library`.
- The container starts with `python manage.py serve`: migrations, sample data on an empty database, then Waitress
  on `0.0.0.0:$PORT`.
- Time zone data comes from the `tzdata` package, so Europe/London works in a slim image.
- A `HEALTHCHECK` calls `/health`.

```bash
docker build -t library-api-django .
docker run --rm -p 8000:8000 -e TEST_MODE=1 library-api-django      # SQLite inside the container
```

---

## What This Version Leaves Out

This is the **basic** version: the contract and nothing more. No authentication, no pagination, no caching, no
events. The advanced copies (security, scale, events, services, operations, delivery) build on it, one idea at a
time. See [Basic and Advanced](https://github.com/devfoundry-training/Library_API_Contract#basic-and-advanced) in
the contract README.

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.13 | Language |
| Django 5.2 (LTS) | Web framework, ORM, migrations, test runner |
| Django REST framework 3.18 | API views, serializers, exception handling |
| dj-database-url 3.1 | `DATABASE_URL` to Django's `DATABASES` |
| psycopg 3.3 | PostgreSQL driver |
| Waitress 3.0 | WSGI server (runs the same on Windows, macOS and Linux) |
| tzdata | Time zone data for Europe/London |
| SQLite 3, PostgreSQL 17 | Databases |
| Docker, Docker Compose | Container image and the PostgreSQL run |
| GitHub Actions | CI |

---

## Related DevFoundry Courses

[Building APIs with FastAPI](https://devfoundry.co.uk/courses/fastapi-apis) ·
[Django Web Development](https://devfoundry.co.uk/courses/django-web-development) ·
[ASP.NET Core Web APIs](https://devfoundry.co.uk/courses/aspnet-core-web-apis) ·
[Database Access with SQLAlchemy](https://devfoundry.co.uk/courses/sqlalchemy-python) ·
[Entity Framework Core](https://devfoundry.co.uk/courses/entity-framework-core)

---

## What's Next?

The same contract in other stacks, each passing the same 60 conformance tests:

- [Library_API_FastAPI](https://github.com/devfoundry-training/Library_API_FastAPI): Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic
- [Library_API_SpringBoot](https://github.com/devfoundry-training/Library_API_SpringBoot): Java 21, Spring Boot 3, Spring Data JPA, Flyway
- [Library_API_DotNet](https://github.com/devfoundry-training/Library_API_DotNet): .NET 10, ASP.NET Core minimal API, EF Core
- [Library_API_Express](https://github.com/devfoundry-training/Library_API_Express): Node.js, Express, TypeScript (later)

Then the advanced roadmap in the [contract README](https://github.com/devfoundry-training/Library_API_Contract#basic-and-advanced):
JWT and roles, pagination and caching, events with an outbox, a split into services behind a gateway, observability,
and Kubernetes delivery.

The library itself comes from the Zero to Hero course family:

- [Python Zero to Hero](https://github.com/devfoundry-training/Python_zero_hero)
- [Java Zero to Hero](https://github.com/devfoundry-training/Java_zero_hero)
- [C# Zero to Hero](https://github.com/devfoundry-training/CS_zero_hero)
