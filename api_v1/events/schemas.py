from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    name: str
    description: str
    latitude: float
    longitude: float


class EventCreate(EventBase):
    created_by: int


class EventUpdate(BaseModel):
    id: int
    name: str | None = None
    description: str | None = None


class Event(EventBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EventsInArea(BaseModel):
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float



class EventNearbyResponse(BaseModel):
    id: int
    name: str
    description: str
    distance: float
    participants: Optional[List[int]] = Field(default_factory=list)
    preview_picture: Optional[str] = None
    created_by: int

    # Настройка для работы с атрибутами SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

class NearbyEventsRequest(BaseModel):
    token: str
    max_distance: int