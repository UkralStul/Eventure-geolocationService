from typing import Annotated

from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from . import crud
from core.models import db_helper, Event


async def event_by_id(
    token: str,
    event_id: Annotated[int, Path],
    session: AsyncSession = Depends(db_helper.session_dependency),
    user_service_url: str = settings.user_service_url,
) -> Event:
    event = await crud.get_event(
        session=session,
        event_id=event_id,
        user_service_url=user_service_url,
        token=token,
    )
    if event is not None:
        return event
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Event not found",
    )
