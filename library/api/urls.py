"""The routes, declared without trailing slashes.

<id:...> only matches a whole number that fits in 32 bits, so /books/abc never
reaches a view and falls through to the JSON 404 (not_found).
"""

from django.conf import settings
from django.urls import path, register_converter

from . import views


class IdConverter:
    regex = "[0-9]+"

    def to_python(self, value: str) -> int:
        number = int(value)
        if number > 2**31 - 1:
            raise ValueError("id out of range")  # Django treats this as no match
        return number

    def to_url(self, value) -> str:
        return str(value)


register_converter(IdConverter, "id")

urlpatterns = [
    path("health", views.HealthView.as_view()),
    path("books", views.BookListView.as_view()),
    path("books/<id:book_id>", views.BookDetailView.as_view()),
    path("members", views.MemberListView.as_view()),
    path("members/<id:member_id>", views.MemberDetailView.as_view()),
    path("members/<id:member_id>/loans", views.MemberLoansView.as_view()),
    path("loans", views.LoanListView.as_view()),
    path("loans/<id:loan_id>", views.LoanDetailView.as_view()),
    path("loans/<id:loan_id>/return", views.LoanReturnView.as_view()),
]

if settings.TEST_MODE:
    urlpatterns.append(path("test/reset", views.TestResetView.as_view()))
