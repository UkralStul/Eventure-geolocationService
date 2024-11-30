from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse

from core.config import settings
from . import crud
from .crud import add_participant_to_event, save_image, get_event_preview
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


@router.post("/in/area/")
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


@router.post("/uploadEventPreview", status_code=status.HTTP_200_OK)
async def upload_event_preview(
    event_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(db_helper.session_dependency),
    user: int = Depends(decode_access_token),
):
    return await save_image(session=session, user_id=user, file=file, event_id=event_id)


@router.get("/preview/{event_id}", response_class=FileResponse)
async def get_preview(
    event_id: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        avatar_path = await get_event_preview(event_id=event_id, session=session)
        if avatar_path.exists():
            return FileResponse(avatar_path, headers={"Cache-Control": "no-store"})
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
        elif e.status_code == 406:
            default_avatar_path = (
                Path(__file__).resolve().parent.parent.parent
                / "uploads/defaults/default-event-preview.jpg"
            )
            if not default_avatar_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Default preview not found",
                )
            return FileResponse(
                default_avatar_path, headers={"Cache-Control": "no-store"}
            )
