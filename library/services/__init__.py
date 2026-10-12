"""Service layer: every business rule from the contract's RULES.md.

Services take plain values (ids, dataclasses, today as a date) and return plain
dataclasses. They never see a request, a status code or SQL, so the unit tests
call them directly with a fixed date.
"""
