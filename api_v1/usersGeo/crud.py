from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api_v1.usersGeo.schemas import UserGeoUpdate
from core.models.UserGeo import UserGeo


async def update_or_create_user_geo(
    user_id: int,
    new_geo: UserGeoUpdate,
    session: AsyncSession,
) -> UserGeo:
    try:
        user_geo = await session.execute(
            select(UserGeo).where(UserGeo.user_id == user_id)
        )
        user_geo = user_geo.scalar_one()

        for name, value in new_geo.model_dump(exclude_unset=True).items():
            setattr(user_geo, name, value)
    except NoResultFound:
        user_geo = UserGeo(user_id=user_id, **new_geo.model_dump())
        session.add(user_geo)

    await session.commit()
    return user_geo


async def get_users_geo(
    user_ids: list[int],
    session: AsyncSession,
) -> list[UserGeo]:
    result = await session.execute(select(UserGeo).where(UserGeo.user_id.in_(user_ids)))
    user_geos = result.scalars().all()
    return list(user_geos)


async def get_users_friend_list(
    user_id: int,
    session: AsyncSession,
):
    pass
