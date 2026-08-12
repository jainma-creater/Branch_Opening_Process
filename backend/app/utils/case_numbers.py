from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BranchOpening


def next_opening_number(db: Session, year: int | None = None) -> str:
    """Generate the next human-readable case number BO-YYYY-NNNN.

    Uniqueness is enforced by the database constraint; callers must retry
    on IntegrityError for concurrent creates.
    """
    year = year or date.today().year
    prefix = f"BO-{year}-"
    count = db.scalar(
        select(func.count(BranchOpening.id)).where(
            BranchOpening.opening_number.like(f"{prefix}%")
        )
    )
    return f"{prefix}{count + 1:04d}"