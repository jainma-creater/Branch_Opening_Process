from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Area, Branch, Region
from app.repositories.organization import AreaRepository, BranchRepository, RegionRepository
from app.schemas.organization import AreaCreate, AreaUpdate, BranchCreate, BranchUpdate, RegionCreate, RegionUpdate


class RegionService:
    def __init__(self, db: Session) -> None:
        self.repo = RegionRepository(db)

    def create(self, data: RegionCreate) -> Region:
        if self.repo.find_by_name(data.name.strip()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Region already exists")
        return self.repo.add(Region(name=data.name.strip(), rent_limit=data.rent_limit))

    def get(self, region_id: int) -> Region:
        region = self.repo.get(region_id)
        if region is None:
            raise HTTPException(status_code=404, detail="Region not found")
        return region

    def list_all(self) -> list[Region]:
        return self.repo.list_all()

    def update(self, region_id: int, data: RegionUpdate) -> Region:
        region = self.get(region_id)
        if data.name is not None and data.name.strip() != region.name:
            if self.repo.find_by_name(data.name.strip()):
                raise HTTPException(status_code=409, detail="Region already exists")
            region.name = data.name.strip()
        if data.rent_limit is not None:
            region.rent_limit = data.rent_limit
        return self.repo.save(region)

    def delete(self, region_id: int) -> None:
        region = self.get(region_id)
        if region.areas:
            raise HTTPException(
                status_code=409,
                detail="Region has areas; cannot delete",
            )
        self.repo.delete(region)


class AreaService:
    def __init__(self, db: Session) -> None:
        self.repo = AreaRepository(db)
        self.regions = RegionRepository(db)

    def create(self, data: AreaCreate) -> Area:
        region = self.regions.get(data.region_id)
        if region is None:
            raise HTTPException(status_code=422, detail="Parent region does not exist")
        if self.repo.find_by_name_in_region(data.region_id, data.name.strip()):
            raise HTTPException(status_code=409, detail="Area already exists in this region")
        return self.repo.add(
            Area(region_id=data.region_id, name=data.name.strip(), rent_limit=data.rent_limit)
        )

    def get(self, area_id: int) -> Area:
        area = self.repo.get(area_id)
        if area is None:
            raise HTTPException(status_code=404, detail="Area not found")
        return area

    def list_all(self, region_id: int | None = None) -> list[Area]:
        if region_id is not None:
            if self.regions.get(region_id) is None:
                raise HTTPException(status_code=404, detail="Region not found")
            return self.repo.list_by_region(region_id)
        return self.repo.list_all()

    def update(self, area_id: int, data: AreaUpdate) -> Area:
        area = self.get(area_id)
        if data.name is not None and data.name.strip() != area.name:
            if self.repo.find_by_name_in_region(area.region_id, data.name.strip()):
                raise HTTPException(status_code=409, detail="Area already exists in this region")
            area.name = data.name.strip()
        if data.rent_limit is not None:
            area.rent_limit = data.rent_limit
        return self.repo.save(area)

    def delete(self, area_id: int) -> None:
        area = self.get(area_id)
        if area.branches:
            raise HTTPException(status_code=409, detail="Area has branches; cannot delete")
        self.repo.delete(area)


class BranchService:
    def __init__(self, db: Session) -> None:
        self.repo = BranchRepository(db)
        self.areas = AreaRepository(db)

    def create(self, data: BranchCreate) -> Branch:
        area = self.areas.get(data.area_id)
        if area is None:
            raise HTTPException(status_code=422, detail="Parent area does not exist")
        if self.repo.find_by_code(data.branch_code.strip()):
            raise HTTPException(status_code=409, detail="Branch code already exists")
        return self.repo.add(
            Branch(
                area_id=data.area_id,
                name=data.name.strip(),
                branch_code=data.branch_code.strip(),
                rent_limit=data.rent_limit,
            )
        )

    def get(self, branch_id: int) -> Branch:
        branch = self.repo.get(branch_id)
        if branch is None:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    def list_all(self, area_id: int | None = None) -> list[Branch]:
        if area_id is not None:
            if self.areas.get(area_id) is None:
                raise HTTPException(status_code=404, detail="Area not found")
            return self.repo.list_by_area(area_id)
        return self.repo.list_all()

    def update(self, branch_id: int, data: BranchUpdate) -> Branch:
        branch = self.get(branch_id)
        if data.name is not None:
            branch.name = data.name.strip()
        if data.branch_code is not None and data.branch_code.strip() != branch.branch_code:
            if self.repo.find_by_code(data.branch_code.strip()):
                raise HTTPException(status_code=409, detail="Branch code already exists")
            branch.branch_code = data.branch_code.strip()
        if data.rent_limit is not None:
            branch.rent_limit = data.rent_limit
        return self.repo.save(branch)

    def delete(self, branch_id: int) -> None:
        branch = self.get(branch_id)
        if branch.openings:
            raise HTTPException(status_code=409, detail="Branch has opening cases; cannot delete")
        self.repo.delete(branch)