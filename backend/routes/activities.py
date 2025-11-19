from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_session
from ..models import Activity, ActivityType, Borough, UnveiledArea, User
from ..schemas import CheckinRequest, GPXUploadResponse

router = APIRouter(prefix="/activities", tags=["activities"])


async def _get_or_create_user(session: AsyncSession, user_id: str) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        user = User(id=user_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@router.post("/gpx", response_model=GPXUploadResponse)
async def upload_gpx(
    borough_id: int,
    file: UploadFile = File(...),
    x_user_id: str = Header(..., alias="X-User-Id"),
    session: AsyncSession = Depends(get_session),
) -> GPXUploadResponse:
    """
    Accept a GPX file upload, associate it with a user, and trigger processing.

    The full Mapbox Map Matching and PostGIS buffer/merge pipeline is left
    as a follow-up implementation detail; this endpoint persists a minimal
    activity record that can be extended.
    """
    settings = get_settings()
    _ = settings  # referenced to avoid 'unused' warnings for now

    user = await _get_or_create_user(session, x_user_id)

    # For now we do not parse the GPX contents here; they can be stored or
    # handed to a background worker in a more advanced setup.
    contents = await file.read()
    raw_ref = f"gpx:{len(contents)}bytes"

    activity = Activity(
        user_id=user.id,
        borough_id=borough_id,
        type=ActivityType.GPX,
        raw_gpx_path=raw_ref,
    )
    session.add(activity)
    await session.commit()
    await session.refresh(activity)

    # TODO: implement Mapbox Map Matching + buffer/merge pipeline.

    return GPXUploadResponse(activity_id=activity.id)


@router.post("/checkin")
async def checkin(
    borough_id: int,
    payload: CheckinRequest,
    x_user_id: str = Header(..., alias="X-User-Id"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Manual check-in endpoint.

    For now, it records an activity and updates the unveiled area using
    a simple PostGIS buffer/union expression if geometry is configured.
    """
    user = await _get_or_create_user(session, x_user_id)

    # Ensure borough exists
    result = await session.execute(select(Borough).where(Borough.id == borough_id))
    borough: Borough | None = result.scalar_one_or_none()
    if borough is None:
        raise RuntimeError("Borough not found")

    # Create a POINT geometry from lat/lon (SRID 4326)
    point_geom = func.ST_SetSRID(
        func.ST_MakePoint(payload.longitude, payload.latitude), 4326
    )

    # 100m buffer around check-in location
    buffer_geom = func.ST_Buffer(
        func.ST_Transform(point_geom, 3857), 100  # approximate in meters
    )
    buffer_geom = func.ST_Transform(buffer_geom, 4326)

    # Intersect with borough geometry and merge into unveiled area
    intersected = func.ST_Intersection(buffer_geom, borough.geometry)

    result = await session.execute(
        select(UnveiledArea).where(
            UnveiledArea.user_id == user.id,
            UnveiledArea.borough_id == borough.id,
        )
    )
    unveiled: UnveiledArea | None = result.scalar_one_or_none()

    if unveiled is None:
        unveiled = UnveiledArea(
            user_id=user.id,
            borough_id=borough.id,
            geometry=intersected,
        )
        session.add(unveiled)
    else:
        merged_geom = func.ST_Union(unveiled.geometry, intersected)
        await session.execute(
            update(UnveiledArea)
                .where(UnveiledArea.id == unveiled.id)
                .values(geometry=merged_geom)
        )

    # Record the check-in activity
    activity = Activity(
        user_id=user.id,
        borough_id=borough.id,
        type=ActivityType.CHECKIN,
    )
    session.add(activity)

    await session.commit()

    return {"status": "ok"}


