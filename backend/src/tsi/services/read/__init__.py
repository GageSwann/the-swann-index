"""Read models for the API: one module per resource, each returning frozen dataclasses.

FastAPI serializes these dataclasses directly and builds the OpenAPI schema from
them, so each response shape is defined once, here.
"""
