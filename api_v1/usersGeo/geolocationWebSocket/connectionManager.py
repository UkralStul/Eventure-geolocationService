from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    # Подключение нового пользователя
    async def connect(self, user_id: str, websocket: WebSocket):
        self.active_connections[user_id] = websocket
        await websocket.accept()

    # Отключение пользователя
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
