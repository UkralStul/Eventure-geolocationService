from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from fastapi import HTTPException, status, UploadFile
from api_v1.events.schemas import EventCreate, EventUpdate, EventsInArea
from core.models import Event
from sqlalchemy import select

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads/avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def get_events(session: AsyncSession) -> list[Event]:
    stmt = select(Event).order_by(Event.id)
    result: Result = await session.execute(stmt)
    events = result.scalars().all()
    return list(events)


async def get_event(
    session: AsyncSession,
    event_id: int,
    user_service_url: str,
    token: str,
) -> Event | None:
    event = await session.get(Event, event_id)

    participant_ids = event.participants if event.participants else []
    print("participant_ids ", participant_ids)
    if participant_ids:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{user_service_url}/auth/getUsersByIds",
                headers=headers,
                json={"ids": participant_ids},
            )
            if response.status_code == 200:
                users_data = response.json()

                # Обновляем участников в event, предполагая, что users_data - это список данных о пользователях
                event.participants = users_data  # Обновляем участников

            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch users data from the microservice",
                )

    return event


async def create_event(session: AsyncSession, event_in: EventCreate) -> Event:
    event = Event(**event_in.model_dump())
    session.add(event)
    await session.commit()
    return event


async def update_event(
    session: AsyncSession,
    event: Event,
    event_update: EventUpdate,
) -> Event:
    for name, value in event_update.model_dump(exclude_unset=True).items():
        setattr(event, name, value)
    await session.commit()
    return event


async def delete_event(
    session: AsyncSession,
    event: Event,
) -> None:
    await session.delete(event)
    await session.commit()


async def events_in_area(
    session: AsyncSession,
    area: EventsInArea,
) -> list[Event]:
    stmt = select(Event).filter(
        Event.latitude >= area.min_latitude,
        Event.latitude <= area.max_latitude,
        Event.longitude >= area.min_longitude,
        Event.longitude <= area.max_longitude,
    )
    result: Result = await session.execute(stmt)
    events = result.scalars().all()
    return list(events)


async def add_participant_to_event(
    event_id: int,
    user_id: int,
    session: AsyncSession,
) -> Event:
    # Получаем ивент по ID
    stmt = select(Event).filter(Event.id == event_id)
    result = await session.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Если participants не существует, создаем пустой список
    if not event.participants:
        event.participants = []

    # Преобразуем participants в список, если это не так
    participants = event.participants if isinstance(event.participants, list) else []

    # Добавляем user_id в список участников, если его нет
    if user_id not in participants:
        participants.append(user_id)
        event.participants = participants
    else:
        raise HTTPException(status_code=400, detail="User is already a participant")

    # Обновляем время изменения события
    event.updated_at = datetime.now()

    # Сохраняем изменения в базе данных
    await session.commit()

    return event


async def save_image(
    session: AsyncSession,
    file: UploadFile,
    event_id: int,
    user_id: int,
) -> Event:
    stmt = select(Event).filter(Event.id == event_id)
    result = await session.execute(stmt)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Could not find event"
        )
    if not event.created_by == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cant modify this event"
        )

    extension = file.filename.split(".")[-1]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{event.id}_event_preview_{timestamp}.{extension}"
    file_location = UPLOAD_DIR / filename

    try:
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    event.preview_picture = filename
    try:
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not update event: {str(e)}")

    return event

#deploy test
async def get_event_preview(
    event_id: int,
    session: AsyncSession,
) -> Path:
    stmt = select(Event).filter(Event.id == event_id)
    result = await session.execute(stmt)
    event = result.scalars().first()
    if event:
        if event.preview_picture:
            return UPLOAD_DIR / event.preview_picture
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Event has no avatar"
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Could not find event"
    )
