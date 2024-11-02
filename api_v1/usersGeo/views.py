from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from .schemas import UserGeo
from . import crud
from .crud import get_users_geo
from .schemas import UserGeoUpdate
from core.models import db_helper
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(tags=["userGeo"])


@router.post("/update_user_geo", response_model=UserGeo)
async def update_or_create_user_geo(
    user_id: int,
    new_geo: UserGeoUpdate,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await crud.update_or_create_user_geo(
        session=session,
        new_geo=new_geo,
        user_id=user_id,
    )


@router.post("/", response_model=List[UserGeo])
async def read_users_geo(
    user_ids: List[int],
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    if not user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="user_ids must not be empty"
        )

    user_geos = await get_users_geo(user_ids=user_ids, session=session)

    if not user_geos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user geos found for the given IDs",
        )

    return user_geos
