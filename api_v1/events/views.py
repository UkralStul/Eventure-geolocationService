from fastapi import APIRouter, HTTPException, status, Depends

from core.config import settings
from . import crud
from .crud import add_participant_to_event
from .schemas import Event, EventCreate, EventUpdate, EventsInArea
from core.models import db_helper
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import event_by_id
from ..auth import decode_access_token

router = APIRouter(tags=["Events"])


@router.get("/", response_model=list[Event])
async def get_events(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await crud.get_events(session=session)


@router.post("/{event_id}/")
async def get_event(
    token: str,
    event_id: int,
    user_service_url: str = settings.user_service_url,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
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


@router.post("/", response_model=Event)
async def create_event(
    event_in: EventCreate,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await crud.create_event(session=session, event_in=event_in)


@router.patch("/{event_id}/")
async def update_event(
    event_update: EventUpdate,
    event: Event = Depends(event_by_id),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await crud.update_event(
        session=session,
        event=event,
        event_update=event_update,
    )


@router.delete("/{event_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event: Event = Depends(event_by_id),
    session: AsyncSession = Depends(db_helper.session_dependency),
) -> None:
    await crud.delete_event(session=session, event=event)


@router.post("/events_in_area/")
async def events_in_area(
    area: EventsInArea,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await crud.events_in_area(area=area, session=session)


@router.post("/addParticipant/{event_id}")
async def add_participant_to_event_view(
    event_id: int,
    token: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user_id = int(decode_access_token(token=token))
    return await add_participant_to_event(
        event_id=event_id, user_id=user_id, session=session
    )
