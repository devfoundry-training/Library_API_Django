"""Request and response shapes.

Input serializers only check JSON types: required fields are present and not
null, whole numbers are real JSON numbers (not "101", true or 4.5), text is text
and dates are real YYYY-MM-DD dates. DRF's own fields coerce types, so these use
strict fields. The value rules (year range, blank text, formats, email shape)
are business rules and live in library/services/validation.py.

Output serializers render the service layer's records.
"""

from rest_framework import serializers

from library.services.records import BookData, MemberData

from .today import parse_iso_date

INT32_MIN, INT32_MAX = -(2**31), 2**31 - 1


class _StrictField(serializers.Field):
    """A field whose messages name the field: "title is required"."""

    def __init__(self, message: str | None = None, **kwargs):
        self.message = message
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        self.error_messages = {**self.error_messages,
                               "required": self.message or f"{field_name} is required",
                               "null": self.message or f"{field_name} is required"}

    def invalid(self, text: str):
        raise serializers.ValidationError(self.message or f"{self.field_name} {text}")

    def to_representation(self, value):
        return value


class StrictInteger(_StrictField):
    def to_internal_value(self, data):
        if type(data) is not int or not INT32_MIN <= data <= INT32_MAX:
            self.invalid("must be a whole number")
        return data


class StrictText(_StrictField):
    """Text exactly as sent: nothing is trimmed."""

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.invalid("must be text")
        return data


class StrictDate(_StrictField):
    def to_internal_value(self, data):
        parsed = parse_iso_date(data) if isinstance(data, str) else None
        if parsed is None:
            self.invalid("must be a date in the form YYYY-MM-DD")
        return parsed


class QueryWholeNumber(_StrictField):
    def to_internal_value(self, data):
        text = data.removeprefix("-")
        if not (text.isascii() and text.isdigit()) or not INT32_MIN <= int(data) <= INT32_MAX:
            self.invalid("must be a whole number")
        return int(data)


class QueryTrueFalse(_StrictField):
    def to_internal_value(self, data):
        if data not in ("true", "false"):
            self.invalid("must be true or false")
        return data == "true"


# -- requests -----------------------------------------------------------------

class BookInput(serializers.Serializer):
    title = StrictText()
    author = StrictText()
    year = StrictInteger()
    genre = StrictText()
    copies = StrictInteger()
    format = StrictText()
    length = StrictInteger()

    def to_data(self) -> BookData:
        return BookData(**self.validated_data)


class MemberCreateInput(serializers.Serializer):
    name = StrictText()
    email = StrictText()
    type = StrictText()
    joined = StrictDate(required=False)

    def to_data(self) -> MemberData:
        return MemberData(**self.validated_data)


class MemberUpdateInput(MemberCreateInput):
    joined = StrictDate()


LOAN_BODY_MESSAGE = "body must be a JSON object with whole-number member_id and book_id"


class LoanInput(serializers.Serializer):
    member_id = StrictInteger(message=LOAN_BODY_MESSAGE)
    book_id = StrictInteger(message=LOAN_BODY_MESSAGE)


class LoanQuery(serializers.Serializer):
    member_id = QueryWholeNumber(required=False)
    active = QueryTrueFalse(required=False)
    overdue = QueryTrueFalse(required=False)


class MemberLoanQuery(serializers.Serializer):
    active = QueryTrueFalse(required=False)
    overdue = QueryTrueFalse(required=False)


# -- responses ----------------------------------------------------------------

class BookOutput(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    author = serializers.CharField()
    year = serializers.IntegerField()
    genre = serializers.CharField()
    copies = serializers.IntegerField()
    format = serializers.CharField()
    length = serializers.IntegerField()
    available = serializers.IntegerField()


class MemberOutput(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()
    type = serializers.CharField()
    joined = serializers.DateField()


class LoanOutput(serializers.Serializer):
    id = serializers.IntegerField()
    book_id = serializers.IntegerField()
    member_id = serializers.IntegerField()
    borrowed = serializers.DateField()
    due = serializers.DateField()
    returned = serializers.DateField(allow_null=True)
    overdue = serializers.BooleanField()
    days_late = serializers.IntegerField()
    fine = serializers.IntegerField()
