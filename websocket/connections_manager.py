# app/connection_manager.py

from typing import Dict, List
from fastapi import WebSocket
 
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, room: str, websocket: WebSocket):
        # await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        self.active_connections[room].remove(websocket)
        if not self.active_connections[room]:
            del self.active_connections[room]

    # async def broadcast(self, room: str, message: dict):
    #     for connection in self.active_connections.get(room, []):
    #         await connection.send_json(message)

    # async def broadcast(self, room: str, message: dict):
    #     connections = self.active_connections.get(room, [])
    #     to_remove = []
    #     for connection in connections:
    #         try:
    #             await connection.send_json(message)
    #         except Exception:
    #             to_remove.append(connection)
    #     for connection in to_remove:
    #         self.disconnect(room, connection)


    async def broadcast(self, room: str, message: dict):
        connections = self.active_connections.get(room, [])
        for connection in connections:
            await connection.send_json(message)



            