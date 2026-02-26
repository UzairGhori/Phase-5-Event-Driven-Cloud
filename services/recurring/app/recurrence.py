# Task: T-A014 — Recurrence date computation logic
# Spec: §12 US2 (Recurring Task Lifecycle), FR-031
# Plan: §2.4 (Internal Flow)

from datetime import datetime, timedelta
from typing import Optional
from calendar import monthrange


def compute_next_due_date(
    current_due_date: datetime,
    pattern: str,
    interval: int = 1,
    ends_at: Optional[datetime] = None,
) -> Optional[datetime]:
    """Compute the next due date based on recurrence pattern.

    FR-031: Completion-based trigger. Supports daily, weekly, monthly
    with configurable interval.

    Returns None if next date exceeds ends_at.

    Examples:
        compute_next_due_date(2026-02-28, "weekly", 1) → 2026-03-07
        compute_next_due_date(2026-02-28, "weekly", 2) → 2026-03-14
        compute_next_due_date(2026-02-28, "daily", 1)  → 2026-03-01
        compute_next_due_date(2026-02-28, "monthly", 1) → 2026-03-28
    """
    if pattern == "daily":
        next_date = current_due_date + timedelta(days=interval)
    elif pattern == "weekly":
        next_date = current_due_date + timedelta(weeks=interval)
    elif pattern == "monthly":
        # Advance by N months, handle end-of-month edge cases
        month = current_due_date.month
        year = current_due_date.year
        day = current_due_date.day

        total_months = month + interval
        new_year = year + (total_months - 1) // 12
        new_month = ((total_months - 1) % 12) + 1
        max_day = monthrange(new_year, new_month)[1]
        new_day = min(day, max_day)

        next_date = current_due_date.replace(
            year=new_year, month=new_month, day=new_day
        )
    else:
        return None

    if ends_at is not None and next_date > ends_at:
        return None

    return next_date
