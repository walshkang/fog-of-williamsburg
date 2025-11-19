import json

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Borough
from ..schemas import BoroughBase, BoroughDetail

router = APIRouter(prefix="/boroughs", tags=["boroughs"])


@router.get("/", response_model=list[BoroughBase])
async def list_boroughs(session: AsyncSession = Depends(get_session)) -> list[BoroughBase]:
    """Return all configured boroughs without heavy geometry payloads."""
    result = await session.execute(select(Borough.id, Borough.name))
    rows = result.all()
    return [BoroughBase(id=row.id, name=row.name) for row in rows]


@router.get("/{borough_id}", response_model=BoroughDetail)
async def get_borough(
    borough_id: int, session: AsyncSession = Depends(get_session)
) -> BoroughDetail:
    """Return a single borough including geometry and total area."""
    result = await session.execute(
        select(
            Borough.id,
            Borough.name,
            Borough.total_area,
            func.ST_AsGeoJSON(Borough.geometry),
        ).where(Borough.id == borough_id)
    )
    row = result.one_or_none()
    if row is None:
        raise RuntimeError("Borough not found")

    geojson_raw: str | None = row[3]
    geometry = json.loads(geojson_raw) if geojson_raw else None

    return BoroughDetail(
        id=row.id,
        name=row.name,
        total_area=row.total_area,
        geometry=geometry,
    )


