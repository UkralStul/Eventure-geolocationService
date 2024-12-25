from datetime import datetime

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import DECIMAL, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from core.models import Base


class UserGeo(Base):
    __tablename__ = "UsersGeo"
    user_id: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    location: Mapped[str] = mapped_column(Geometry(geometry_type='POINT', srid=4326))

    def to_dict(self):
        point = to_shape(self.location)  # Преобразуем Geometry в объект Point
        return {
            "user_id": self.user_id,
            "latitude": point.y,
            "longitude": point.x,
            "updated_at": self.updated_at,
        }
