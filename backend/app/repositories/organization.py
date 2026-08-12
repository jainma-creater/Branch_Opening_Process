from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Area, Branch, Region


class RegionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, region_id: int) -> Region | None:
        return self.db.get(Region, region_id)

    def find_by_name(self, name: str) -> Region | None:
        return self.db.scalar(select(Region).where(Region.name == name))

    def list_all(self) -> list[Region]:
        return list(self.db.scalars(select(Region).order_by(Region.name)).all())

    def add(self, region: Region) -> Region:
        self.db.add(region)
        self.db.commit()
        self.db.refresh(region)
        return region

    def save(self, region: Region) -> Region:
        self.db.commit()
        self.db.refresh(region)
        return region

    def delete(self, region: Region) -> None:
        self.db.delete(region)
        self.db.commit()


class AreaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, area_id: int) -> Area | None:
        return self.db.get(Area, area_id)

    def find_by_name_in_region(self, region_id: int, name: str) -> Area | None:
        return self.db.scalar(
            select(Area).where(Area.region_id == region_id, Area.name == name)
        )

    def list_by_region(self, region_id: int) -> list[Area]:
        return list(
            self.db.scalars(
                select(Area).where(Area.region_id == region_id).order_by(Area.name)
            ).all()
        )

    def list_all(self) -> list[Area]:
        return list(self.db.scalars(select(Area).order_by(Area.name)).all())

    def add(self, area: Area) -> Area:
        self.db.add(area)
        self.db.commit()
        self.db.refresh(area)
        return area

    def save(self, area: Area) -> Area:
        self.db.commit()
        self.db.refresh(area)
        return area

    def delete(self, area: Area) -> None:
        self.db.delete(area)
        self.db.commit()


class BranchRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, branch_id: int) -> Branch | None:
        return self.db.get(Branch, branch_id)

    def find_by_code(self, code: str) -> Branch | None:
        return self.db.scalar(select(Branch).where(Branch.branch_code == code))

    def list_by_area(self, area_id: int) -> list[Branch]:
        return list(
            self.db.scalars(
                select(Branch).where(Branch.area_id == area_id).order_by(Branch.name)
            ).all()
        )

    def list_all(self) -> list[Branch]:
        return list(self.db.scalars(select(Branch).order_by(Branch.name)).all())

    def add(self, branch: Branch) -> Branch:
        self.db.add(branch)
        self.db.commit()
        self.db.refresh(branch)
        return branch

    def save(self, branch: Branch) -> Branch:
        self.db.commit()
        self.db.refresh(branch)
        return branch

    def delete(self, branch: Branch) -> None:
        self.db.delete(branch)
        self.db.commit()