from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    rent_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    areas: Mapped[list["Area"]] = relationship(back_populates="region")


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    rent_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    region: Mapped[Region] = relationship(back_populates="areas")
    branches: Mapped[list["Branch"]] = relationship(back_populates="area")


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    branch_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    rent_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    area: Mapped[Area] = relationship(back_populates="branches")
    openings: Mapped[list["BranchOpening"]] = relationship(back_populates="branch")


from app.models.opening import BranchOpening  # noqa: E402
