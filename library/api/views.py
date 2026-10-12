"""The API views: read the request, call one service function, shape the answer.

APIView classes, not ModelViewSet: a viewset would talk to the ORM directly and
skip the service layer, where the rules are. No view decides a rule.
"""

from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from library.services import books, health, loans, members, sample_data

from . import serializers as s
from .today import today_for


def json_object(request: Request, message: str = "body must be a JSON object") -> dict:
    data = request.data
    if not isinstance(data, dict):
        raise ValidationError(message)
    return data


def valid(serializer_class, data):
    """Run an input serializer; a failure raises ValidationError (400)."""
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer


def created(output, record, path: str) -> Response:
    return Response(output(record).data, status=201, headers={"Location": path})


class LibraryView(APIView):
    """Every endpoint works out today first, so a bad X-Today is 400 everywhere."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.today = today_for(request)


class HealthView(LibraryView):
    def get(self, request):
        return Response({"status": health.check()})


class BookListView(LibraryView):
    def get(self, request):
        params = request.query_params
        found = books.list_books(title=params.get("title"), author=params.get("author"),
                                 genre=params.get("genre"))
        return Response(s.BookOutput(found, many=True).data)

    def post(self, request):
        data = valid(s.BookInput, json_object(request)).to_data()
        book = books.create_book(data)
        return created(s.BookOutput, book, f"/books/{book.id}")


class BookDetailView(LibraryView):
    def get(self, request, book_id: int):
        return Response(s.BookOutput(books.get_book(book_id)).data)

    def put(self, request, book_id: int):
        data = valid(s.BookInput, json_object(request)).to_data()
        return Response(s.BookOutput(books.update_book(book_id, data)).data)

    def delete(self, request, book_id: int):
        books.delete_book(book_id)
        return Response(status=204)


class MemberListView(LibraryView):
    def get(self, request):
        return Response(s.MemberOutput(members.list_members(), many=True).data)

    def post(self, request):
        data = valid(s.MemberCreateInput, json_object(request)).to_data()
        member = members.create_member(data, self.today)
        return created(s.MemberOutput, member, f"/members/{member.id}")


class MemberDetailView(LibraryView):
    def get(self, request, member_id: int):
        return Response(s.MemberOutput(members.get_member(member_id)).data)

    def put(self, request, member_id: int):
        data = valid(s.MemberUpdateInput, json_object(request)).to_data()
        return Response(s.MemberOutput(members.update_member(member_id, data)).data)


class MemberLoansView(LibraryView):
    def get(self, request, member_id: int):
        query = valid(s.MemberLoanQuery, request.query_params.dict()).validated_data
        found = members.list_member_loans(member_id, self.today, **query)
        return Response(s.LoanOutput(found, many=True).data)


class LoanListView(LibraryView):
    def get(self, request):
        query = valid(s.LoanQuery, request.query_params.dict()).validated_data
        return Response(s.LoanOutput(loans.list_loans(self.today, **query), many=True).data)

    def post(self, request):
        body = valid(s.LoanInput, json_object(request, s.LOAN_BODY_MESSAGE)).validated_data
        loan = loans.borrow(body["member_id"], body["book_id"], self.today)
        return created(s.LoanOutput, loan, f"/loans/{loan.id}")


class LoanDetailView(LibraryView):
    def get(self, request, loan_id: int):
        return Response(s.LoanOutput(loans.get_loan(loan_id, self.today)).data)


class LoanReturnView(LibraryView):
    def post(self, request, loan_id: int):
        return Response(s.LoanOutput(loans.return_loan(loan_id, self.today)).data)


class TestResetView(APIView):
    """POST /test/reset. Only routed when TEST_MODE=1 (see urls.py)."""

    def post(self, request):
        sample_data.reset()
        return Response(status=204)
