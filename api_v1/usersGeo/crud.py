import httpx
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func
from api_v1.auth import decode_access_token
from api_v1.usersGeo.schemas import UserGeoUpdate, UserGeoResponce
from core.models.UserGeo import UserGeo
from fastapi import status, HTTPException


async def update_or_create_user_geo(
    user_id: int,
    new_geo: UserGeoUpdate,
    session: AsyncSession,
) -> dict:
    try:
        user_geo = await session.execute(
            select(UserGeo).where(UserGeo.user_id == user_id)
        )
        user_geo = user_geo.scalar_one()

        # Обновляем координаты
        if new_geo.latitude and new_geo.longitude:
            user_geo.location = f"POINT({new_geo.longitude} {new_geo.latitude})"
    except NoResultFound:
        location = f"POINT({new_geo.longitude} {new_geo.latitude})"
        user_geo = UserGeo(user_id=user_id, location=location)
        session.add(user_geo)

    await session.commit()
    await session.refresh(user_geo)  # Обновляем объект из базы
    return user_geo.to_dict()  # Возвращаем данные как словарь


async def get_users_geo(
    user_ids: list[int],
    session: AsyncSession,
) -> list[dict]:
    result = await session.execute(select(UserGeo).where(UserGeo.user_id.in_(user_ids)))
    user_geos = result.scalars().all()

    return [user_geo.to_dict() for user_geo in user_geos]



async def get_friend_list(
    token: str,
    user_service_url: str,
):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{user_service_url}/api/v1/friends/friendsList",
            headers=headers,
        )

    if response.status_code == 200:
        friend_ids = response.json()
        return friend_ids
    elif response.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    else:
        raise Exception("Не удалось получить список друзей пользователя")


async def get_users_friends_geo(
    token: str,
    session: AsyncSession,
    user_service_url: str,
) -> list[dict]:
    friend_ids = await get_friend_list(token=token, user_service_url=user_service_url)

    friends_geo = await get_users_geo(user_ids=friend_ids, session=session)

    return friends_geo


async def get_nearby_users(
    token: str,
    session: AsyncSession,
    max_distance: float = 5000,  # Максимальное расстояние в метрах
) -> list[dict]:
    try:
        user_id = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Получаем координаты текущего пользователя
    user_geo = await session.execute(
        select(UserGeo).where(UserGeo.user_id == user_id)
    )
    user_geo = user_geo.scalar_one_or_none()

    if not user_geo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User location not found",
        )

    # Находим ближайших пользователей
    query = (
        select(
            UserGeo.user_id,
            func.ST_DistanceSphere(
                UserGeo.location, user_geo.location
            ).label("distance")
        )
        .where(UserGeo.user_id != user_id)  # Исключаем самого пользователя
        .where(
            func.ST_DWithin(
                UserGeo.location, user_geo.location, max_distance
            )
        )  # Условие на расстояние
        .order_by("distance")
        .limit(5)
    )

    result = await session.execute(query)
    nearby_users = result.fetchall()

    return [
        {"user_id": row.user_id, "distance": row.distance}
        for row in nearby_users
    ]
