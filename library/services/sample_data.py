"""The sample data: loaded on an empty database, and put back by POST /test/reset."""

from library.repositories import sample_data as sample_repo


def reset() -> None:
    """Empty the three tables, load the sample data, and make the next ids book 21, member 110, loan 13."""
    sample_repo.load(clear=True)


def load_if_empty() -> bool:
    """Load the sample data when there are no books, members or loans. True when it loaded."""
    if not sample_repo.is_empty():
        return False
    sample_repo.load(clear=False)
    return True
