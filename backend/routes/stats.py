from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Borough, UnveiledArea, User
from ..schemas import CoreScore

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/core-score", response_model=CoreScore)
async def core_score(
    x_user_id: str = Header(..., alias="X-User-Id"),
    session: AsyncSession = Depends(get_session),
) -> CoreScore:
    """
    Return the user's core exploration score for their chosen borough.
    """
    result = await session.execute(select(User).where(User.id == x_user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None or user.chosen_borough_id is None:
        raise RuntimeError("User or chosen borough not found")

    result = await session.execute(
        select(Borough).where(Borough.id == user.chosen_borough_id)
    )
    borough: Borough | None = result.scalar_one_or_none()
    if borough is None:
        raise RuntimeError("Borough not found")

    result = await session.execute(
        select(UnveiledArea).where(
            UnveiledArea.user_id == user.id,
            UnveiledArea.borough_id == borough.id,
        )
    )
    unveiled: UnveiledArea | None = result.scalar_one_or_none()

    if unveiled is None:
        unveiled_area = 0.0
    else:
        # Compute area using PostGIS ST_Area, with projection suitable for meters.
        area_expr = func.ST_Area(func.ST_Transform(unveiled.geometry, 3857))
        area_result = await session.execute(select(area_expr))
        unveiled_area = float(area_result.scalar_one() or 0.0)

    percent = 0.0
    if borough.total_area > 0:
        percent = (unveiled_area / borough.total_area) * 100.0

    return CoreScore(
        borough_id=borough.id,
        borough_name=borough.name,
        percent_explored=percent,
        total_area=borough.total_area,
        unveiled_area=unveiled_area,
    )


