"""Repository layer: thin query and save functions over the Django ORM.

Repositories answer questions ("how many open loans has member 105?") and store
changes. They never decide anything about the rules: that is the service layer.
"""
