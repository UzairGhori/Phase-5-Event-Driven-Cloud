# Task: T-A009 — Full-text search helper for tsvector
# Spec: §11.1 (search param), FR-035, SC-019
# Plan: §2.1 (Query Parameters), §8 (search/tsvector.py)

import re

from sqlalchemy import func, text


def build_tsquery(search_term: str) -> str:
    """Convert user search input to PostgreSQL tsquery string.

    Uses 'english' configuration for stemming (Spec Clarification #11).
    Splits input into words and joins with & (AND) for multi-word queries.
    Sanitizes input to prevent SQL injection.
    """
    words = re.findall(r"\w+", search_term.strip())
    if not words:
        return ""
    sanitized = [word.replace("'", "''") for word in words]
    return " & ".join(sanitized)


def search_filter(search_term: str):
    """Return a SQLAlchemy filter clause for tsvector search.

    Uses to_tsquery('english', ...) against search_vector column.
    """
    tsquery = build_tsquery(search_term)
    if not tsquery:
        return None
    return text(
        "search_vector @@ to_tsquery('english', :query)"
    ).bindparams(query=tsquery)
