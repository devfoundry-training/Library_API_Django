"""The one place that answers "what is today".

1. The X-Today header, only when TEST_MODE=1 (a bad value is 400).
2. The LIBRARY_TODAY environment variable (read once in settings).
3. The current date in Europe/London.

Views call it once per request and pass the date to the service layer.
"""

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from rest_framework.exceptions import ValidationError

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def parse_iso_date(text: str) -> date | None:
    """A real date written exactly YYYY-MM-DD, or None."""
    if not DATE_PATTERN.fullmatch(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def today_for(request) -> date:
    if settings.TEST_MODE:
        header = request.headers.get("X-Today")
        if header is not None:
            today = parse_iso_date(header)
            if today is None:
                raise ValidationError("X-Today must be a date in the form YYYY-MM-DD")
            return today
    if settings.LIBRARY_TODAY is not None:
        return settings.LIBRARY_TODAY
    return datetime.now(ZoneInfo(settings.LIBRARY_TIME_ZONE)).date()
