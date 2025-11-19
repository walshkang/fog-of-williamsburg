from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import User
from ..schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead)
async def create_or_update_user(
    payload: UserCreate, session: AsyncSession = Depends(get_session)
) -> UserRead:
    """
    Create a new anonymous user or update their chosen borough.

    The client is responsible for generating and persisting the `id`
    (e.g., a UUID stored in local storage on the device).
    """
    result = await session.execute(select(User).where(User.id == payload.id))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        user = User(id=payload.id, chosen_borough_id=payload.chosen_borough_id)
        session.add(user)
    else:
        user.chosen_borough_id = payload.chosen_borough_id

    await session.commit()
    await session.refresh(user)
    return UserRead.from_orm(user)


