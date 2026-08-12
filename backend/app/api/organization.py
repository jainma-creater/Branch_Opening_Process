from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.organization import (
    AreaCreate,
    AreaRead,
    AreaUpdate,
    BranchCreate,
    BranchRead,
    BranchUpdate,
    RegionCreate,
    RegionRead,
    RegionUpdate,
)
from app.services.organization import AreaService, BranchService, RegionService

router = APIRouter(prefix="/organization", tags=["Organization"])

WRITE_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


def _region_read(region, db: Session) -> RegionRead:
    return RegionRead(
        id=region.id,
        name=region.name,
        rent_limit=region.rent_limit,
        area_count=len(region.areas),
        branch_count=sum(len(a.branches) for a in region.areas),
    )


@router.get("/regions", response_model=list[RegionRead])
def list_regions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RegionRead]:
    regions = RegionService(db).list_all()
    return [_region_read(r, db) for r in regions]


@router.get("/regions/{region_id}", response_model=RegionRead)
def get_region(
    region_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RegionRead:
    return _region_read(RegionService(db).get(region_id), db)


@router.post("/regions", response_model=RegionRead, status_code=status.HTTP_201_CREATED)
def create_region(
    data: RegionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> RegionRead:
    return _region_read(RegionService(db).create(data), db)


@router.patch("/regions/{region_id}", response_model=RegionRead)
def update_region(
    region_id: int,
    data: RegionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> RegionRead:
    return _region_read(RegionService(db).update(region_id, data), db)


@router.delete("/regions/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(
    region_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> None:
    RegionService(db).delete(region_id)


@router.get("/areas", response_model=list[AreaRead])
def list_areas(
    region_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AreaRead]:
    return AreaService(db).list_all(region_id)


@router.get("/areas/{area_id}", response_model=AreaRead)
def get_area(
    area_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AreaRead:
    area = AreaService(db).get(area_id)
    return AreaRead(
        id=area.id,
        region_id=area.region_id,
        name=area.name,
        rent_limit=area.rent_limit,
        branch_count=len(area.branches),
    )


@router.post("/areas", response_model=AreaRead, status_code=status.HTTP_201_CREATED)
def create_area(
    data: AreaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> AreaRead:
    area = AreaService(db).create(data)
    return AreaRead(
        id=area.id,
        region_id=area.region_id,
        name=area.name,
        rent_limit=area.rent_limit,
        branch_count=0,
    )


@router.patch("/areas/{area_id}", response_model=AreaRead)
def update_area(
    area_id: int,
    data: AreaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> AreaRead:
    area = AreaService(db).update(area_id, data)
    return AreaRead(
        id=area.id,
        region_id=area.region_id,
        name=area.name,
        rent_limit=area.rent_limit,
        branch_count=len(area.branches),
    )


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_area(
    area_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> None:
    AreaService(db).delete(area_id)


@router.get("/branches", response_model=list[BranchRead])
def list_branches(
    area_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[BranchRead]:
    return BranchService(db).list_all(area_id)


@router.get("/branches/{branch_id}", response_model=BranchRead)
def get_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BranchRead:
    return BranchService(db).get(branch_id)


@router.post("/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(
    data: BranchCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> BranchRead:
    return BranchService(db).create(data)


@router.patch("/branches/{branch_id}", response_model=BranchRead)
def update_branch(
    branch_id: int,
    data: BranchUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> BranchRead:
    return BranchService(db).update(branch_id, data)


@router.delete("/branches/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*WRITE_ROLES)),
) -> None:
    BranchService(db).delete(branch_id)