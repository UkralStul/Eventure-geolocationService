from fastapi import APIRouter, Depends
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from .connectionManager import ConnectionManager
from core.models import db_helper
from api_v1.usersGeo.crud import update_or_create_user_geo, get_users_geo
from api_v1.usersGeo.schemas import UserGeoUpdate

router = APIRouter(tags=["ws"])
manager = ConnectionManager()


@router.get("/kakish")
async def get_kakish():
    return {"message": "kakish"}


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    # Присоединение нового пользователя
    await websocket.accept()
    print(f"User {user_id} connected")
    manager.active_connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            action = data.get("action")

            if action == "update_geo":
                # Получаем новые геоданные пользователя
                geo_data = UserGeoUpdate(**data["geo"])
                print("geo data", geo_data)
                await update_or_create_user_geo(user_id, geo_data, session)

            elif action == "get_user_geos":
                # Получаем ID пользователей, чьи геоданные нужны
                user_ids = data.get("user_ids", [])
                user_geos = await get_users_geo(user_ids, session)
                await websocket.send_json({"user_geos": user_geos})

    except WebSocketDisconnect:
        # Обрабатываем отключение клиента
        del manager.active_connections[user_id]
