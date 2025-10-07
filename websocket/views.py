# import os
# import django

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vihaan.settings")
# django.setup()

# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
# from fastapi.security import HTTPBearer
# from jose import JWTError, jwt
# from django.conf import settings

# from .models import *
# from .serializers import *
# from app.connection_manager import ConnectionManager
# from init_django import *  # Check this for duplication

# app = FastAPI()
# manager = ConnectionManager()
# ROOM = "default"
# security = HTTPBearer()

# SECRET_KEY = settings.SECRET_KEY
# ALGORITHM = "HS256"

# def get_current_user(token=Depends(security)):
#     try:
#         payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("user_id")
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid user_id in token")
#         return user_id
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token or expired")

# def get_model_and_serializer(name: str):
#     mapping = {
#         "purchase_order": (purchaseorder_table, PurchaseOrderSerializer),
#         "purchase_order_item": (purchaseorder_item_table, PurchaseOrderItemSerializer),
#         "packing": (packing_table, PackingSerializer),
#         "box_packing": (box_packing_table, BoxPackingSerializer),
#         "delivery": (delivery_table, DeliverySerializer),
#     }
#     return mapping.get(name)


# # fastapi_app.py

# import os
# import django
# import json

# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
# from fastapi.security import HTTPBearer
# from jose import JWTError, jwt
# from django.conf import settings

# # Django setup
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vihaan.settings")
# django.setup()

# # Import Django models and serializers
# from app.models import (
#     purchaseorder_table, purchaseorder_item_table,
#     packing_table, box_packing_table, delivery_table
# )

# from app.serializers import (
#     PurchaseOrderSerializer, PurchaseOrderItemSerializer,
#     PackingSerializer, BoxPackingSerializer, DeliverySerializer
# )

# # --- WebSocket Connection Manager ---
# from typing import Dict, List

# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: Dict[str, List[WebSocket]] = {}

#     async def connect(self, room: str, websocket: WebSocket):
#         await websocket.accept()
#         if room not in self.active_connections:
#             self.active_connections[room] = []
#         self.active_connections[room].append(websocket)

#     def disconnect(self, room: str, websocket: WebSocket):
#         self.active_connections[room].remove(websocket)
#         if not self.active_connections[room]:
#             del self.active_connections[room]

#     async def broadcast(self, room: str, message: dict):
#         for connection in self.active_connections.get(room, []):
#             await connection.send_json(message)

# # --- App & Auth Setup ---
# app = FastAPI()
# manager = ConnectionManager()
# ROOM = "default"
# security = HTTPBearer()

# SECRET_KEY = settings.SECRET_KEY
# ALGORITHM = "HS256"

# def get_current_user(token=Depends(security)):
#     try:
#         payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("user_id")
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid user_id in token")
#         return user_id
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

# # --- Model/Serializer Mapping ---
# def get_model_and_serializer(name: str):
#     mapping = {
#         "purchase_order": (purchaseorder_table, PurchaseOrderSerializer),
#         "purchase_order_item": (purchaseorder_item_table, PurchaseOrderItemSerializer),
#         "packing": (packing_table, PackingSerializer),
#         "box_packing": (box_packing_table, BoxPackingSerializer),
#         "delivery": (delivery_table, DeliverySerializer),
#     }
#     return mapping.get(name)

# # --- CRUD Endpoints ---
# @app.post("/{model_name}/add/")
# async def create_record(model_name: str, request: Request, user_id=Depends(get_current_user)):
#     model_serializer = get_model_and_serializer(model_name)
#     if not model_serializer:
#         raise HTTPException(404, detail="Invalid model")

#     model, serializer_class = model_serializer
#     data = await request.json()
#     serializer = serializer_class(data=data)
#     if serializer.is_valid():
#         instance = serializer.save(created_by=user_id, updated_by=user_id)
#         await manager.broadcast(ROOM, {
#             "event": f"{model_name}_created",
#             "data": serializer_class(instance).data
#         })
#         return serializer_class(instance).data
#     return {"errors": serializer.errors}

# @app.put("/{model_name}/edit/{pk}/")
# async def update_record(model_name: str, pk: int, request: Request, user_id=Depends(get_current_user)):
#     model_serializer = get_model_and_serializer(model_name)
#     if not model_serializer:
#         raise HTTPException(404, detail="Invalid model")

#     model, serializer_class = model_serializer
#     try:
#         instance = model.objects.get(pk=pk)
#     except model.DoesNotExist:
#         raise HTTPException(404, detail="Record not found")

#     data = await request.json()
#     serializer = serializer_class(instance, data=data, partial=True)
#     if serializer.is_valid():
#         updated = serializer.save(updated_by=user_id)
#         await manager.broadcast(ROOM, {
#             "event": f"{model_name}_updated",
#             "data": serializer_class(updated).data
#         })
#         return serializer_class(updated).data
#     return {"errors": serializer.errors}

# @app.delete("/{model_name}/delete/{pk}/")
# async def delete_record(model_name: str, pk: int, user_id=Depends(get_current_user)):
#     model_serializer = get_model_and_serializer(model_name)
#     if not model_serializer:
#         raise HTTPException(404, detail="Invalid model")

#     model, serializer_class = model_serializer
#     try:
#         instance = model.objects.get(pk=pk)
#         data = serializer_class(instance).data
#         instance.delete()
#         await manager.broadcast(ROOM, {
#             "event": f"{model_name}_deleted",
#             "data": data
#         })
#         return {"detail": "Deleted"}
#     except model.DoesNotExist:
#         raise HTTPException(404, detail="Record not found")

# @app.get("/{model_name}/list/")
# async def list_records(model_name: str, user_id=Depends(get_current_user)):
#     model_serializer = get_model_and_serializer(model_name)
#     if not model_serializer:
#         raise HTTPException(404, detail="Invalid model")

#     model, serializer_class = model_serializer
#     queryset = model.objects.all().order_by("-id")
#     return serializer_class(queryset, many=True).data

# # --- WebSocket Endpoint ---
# @app.websocket("/ws/")
# async def websocket_endpoint(websocket: WebSocket, token: str = ""):
#     # Optionally verify token here (advanced use)
#     await websocket.accept()
#     await manager.connect(ROOM, websocket)
#     try:
#         while True:
#             await websocket.receive_text()  # no processing for now
#     except WebSocketDisconnect:
#         manager.disconnect(ROOM, websocket)


def home(request):
    return (request,"index3.html")