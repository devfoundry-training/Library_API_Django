"""The service layer's exceptions. Each carries the contract's error code and message.

The API layer maps the three families to a status: InvalidInput 400, NotFound 404,
Conflict 409. The services themselves know nothing about HTTP.
"""


class LibraryError(Exception):
    code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidInput(LibraryError):
    code = "validation_error"


class NotFound(LibraryError):
    pass


class Conflict(LibraryError):
    pass


class BookNotFound(NotFound):
    code = "book_not_found"

    def __init__(self, book_id: int):
        super().__init__(f"no book with id {book_id}")


class MemberNotFound(NotFound):
    code = "member_not_found"

    def __init__(self, member_id: int):
        super().__init__(f"no member with id {member_id}")


class LoanNotFound(NotFound):
    code = "loan_not_found"

    def __init__(self, loan_id: int):
        super().__init__(f"no loan with id {loan_id}")


class LoanLimitReached(Conflict):
    code = "loan_limit_reached"

    def __init__(self, name: str, open_loans: int, limit: int):
        super().__init__(f"{name} already has {open_loans} loans (limit {limit})")


class NoCopiesAvailable(Conflict):
    code = "no_copies_available"

    def __init__(self, title: str):
        super().__init__(f"{title} has no copies available")


class AlreadyReturned(Conflict):
    code = "already_returned"

    def __init__(self, loan_id: int):
        super().__init__(f"loan {loan_id} has already been returned")


class ReturnBeforeBorrowed(Conflict):
    code = "return_before_borrowed"

    def __init__(self, loan_id: int, borrowed, today):
        super().__init__(f"loan {loan_id} was borrowed on {borrowed.isoformat()} "
                         f"and cannot be returned on {today.isoformat()}")


class CopiesBelowOnLoan(Conflict):
    code = "copies_below_on_loan"

    def __init__(self, on_loan: int):
        super().__init__(f"copies cannot be less than the {on_loan} on loan")


class BookHasLoans(Conflict):
    code = "book_has_loans"

    def __init__(self, title: str):
        super().__init__(f"{title} has loans and cannot be deleted")


class EmailTaken(Conflict):
    code = "email_taken"

    def __init__(self, email: str, member_id: int):
        super().__init__(f"email {email} is already used by member {member_id}")
