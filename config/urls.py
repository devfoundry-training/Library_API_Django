"""The root URL configuration. The API routes live in library/api/urls.py."""

from django.urls import include, path

urlpatterns = [
    path("", include("library.api.urls")),
]

# Django's own 404 and 500 pages are HTML: these keep every answer in the error format.
handler400 = "library.api.exceptions.bad_request_view"
handler404 = "library.api.exceptions.not_found_view"
handler500 = "library.api.exceptions.server_error_view"
