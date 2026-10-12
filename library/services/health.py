"""GET /health: the server is up and can reach its database."""

from library.repositories import health as health_repo


def check() -> str:
    health_repo.ping()
    return "ok"
