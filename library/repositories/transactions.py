"""Transactions for the service layer, so services need no Django import of their own."""

from django.db import transaction

atomic = transaction.atomic
