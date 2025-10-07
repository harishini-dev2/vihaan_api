import os
from time import timezone
import django

# Setup Django environment (if needed for your project)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vihaan.settings")
django.setup()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends,Body, Query
import json


from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from django.conf import settings

from .models import *
from .db import init_db
from .serializers import *

from typing import Dict, List

from decimal import Decimal


from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError





def serialize_data(obj):
    """
    Recursively converts datetime and Decimal objects in a dict or list to JSON serializable types.
    """
    if isinstance(obj, dict):
        return {k: serialize_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_data(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)  # or str(obj) if you prefer
    return obj


def response_switch(case, message="", data=None, error=None, framework="drf"):
    if framework == "drf":
        from rest_framework import status
        from rest_framework.response import Response

        cases = {
            "success": {"status": "success", "status_code": status.HTTP_200_OK},
            "missing": {"status": "missing", "status_code": status.HTTP_200_OK},
            "created": {"status": "success", "status_code": status.HTTP_201_CREATED},
            "bad_request": {"status": "failed", "status_code": status.HTTP_400_BAD_REQUEST},
            "unauthorized": {"status": "failed", "status_code": status.HTTP_401_UNAUTHORIZED},
            "not_found": {"status": "failed", "status_code": status.HTTP_404_NOT_FOUND},
            "server_error": {"status": "error", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
        }

        config = cases.get(case, cases["success"])

        response_data = {
            "message": message,
            "status": config["status"],
        }

        if isinstance(data, (list, tuple)):
            response_data["count"] = len(data)
            response_data["data"] = data
        elif isinstance(data, dict) and "results" in data:
            response_data["count"] = data.get("count", len(data["results"]))
            response_data["data"] = data
        else:
            response_data["data"] = data

        if error:
            response_data["error"] = error

        return Response(response_data, status=config["status_code"])

    elif framework == "fastapi":
        from fastapi.responses import JSONResponse
        from starlette import status as fast_status

        cases = {
            "success": {"status": "success", "status_code": fast_status.HTTP_200_OK},
            "missing": {"status": "missing", "status_code": fast_status.HTTP_200_OK},
            "created": {"status": "success", "status_code": fast_status.HTTP_201_CREATED},
            "bad_request": {"status": "failed", "status_code": fast_status.HTTP_400_BAD_REQUEST},
            "unauthorized": {"status": "failed", "status_code": fast_status.HTTP_401_UNAUTHORIZED},
            "not_found": {"status": "failed", "status_code": fast_status.HTTP_404_NOT_FOUND},
            "server_error": {"status": "error", "status_code": fast_status.HTTP_500_INTERNAL_SERVER_ERROR},
        }

        config = cases.get(case, cases["success"])

        response_data = {
            "message": message,
            "status": config["status"],
        }

        if isinstance(data, (list, tuple)):
            response_data["count"] = len(data)
            response_data["data"] = data
        elif isinstance(data, dict) and "results" in data:
            response_data["count"] = data.get("count", len(data["results"]))
            response_data["data"] = data
        else:
            response_data["data"] = data

        if error:
            response_data["error"] = error

        return JSONResponse(content=response_data, status_code=config["status_code"])

    else:
        raise ValueError("Invalid framework specified. Choose 'drf' or 'fastapi'.")




# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, room: str, websocket: WebSocket):
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        if room in self.active_connections and websocket in self.active_connections[room]:
            self.active_connections[room].remove(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]

    async def broadcast(self, room: str, message: dict):
        serialized_message = serialize_data(message)
        for connection in self.active_connections.get(room, []):
            await connection.send_json(serialized_message)


app = FastAPI()
init_db(app)
manager = ConnectionManager()
security = HTTPBearer()



SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

def get_current_user(token=Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user_id in token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Mapping model name to (Tortoise model, output Pydantic, input Pydantic)
def get_model_and_serializers(name: str):
    mapping = {
        "purchase_order": (purchaseorder_table, PurchaseOrder_Pydantic, PurchaseOrderIn_Pydantic),
        "purchase_order_item": (purchaseorder_item_table, PurchaseOrderItem_Pydantic, PurchaseOrderItemIn_Pydantic),
        "packing": (packing_table, Packing_Pydantic, PackingIn_Pydantic),
        "box_packing": (boxpacking_table, BoxPacking_Pydantic, BoxPackingIn_Pydantic),
        # "boxpacking_item": (boxpacking_item_table, BoxPackingItem_Pydantic, BoxPackingItemIn_Pydantic),
        "delivery": (delivery_table, Delivery_Pydantic, DeliveryIn_Pydantic),
        # "delivery_item": (delivery_item_table, DeliveryItem_Pydantic, DeliveryItemIn_Pydantic),  
    }
    return mapping.get(name)



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()

    # Check for missing query parameters
    missing_query_params = [err for err in errors if err["loc"][0] == "query" and err["type"] == "missing"]
    if missing_query_params:
        missing_field = missing_query_params[0]["loc"][1]
        message = f"{missing_field} is required in query parameters (?{missing_field}=)"
        return response_switch(
            case="missing",
            message=message,
            data=[],
            framework="fastapi"
        )

    # General validation error fallback
    formatted_errors = []
    for err in errors:
        formatted_errors.append({
            "type": err.get("type"),
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "input": err.get("ctx", None)
        })

    return response_switch(
        case="bad_request",
        message="Validation error",
        error=formatted_errors,
        framework="fastapi"
    )

# ----------- REST API -----------

@app.post("/api/{model_name}/add/")
async def create_record(
    model_name: str,
    request: Request,
    user_id=Depends(get_current_user),
    body: dict = Body(...)
):
    model_info = get_model_and_serializers(model_name)
    if not model_info:
        return response_switch("not_found", message="Invalid model name", framework="fastapi")

    model, OutputSchema, InputSchema = model_info

    # Example: check required fields manually (like your DRF check for name)
    required_fields = ["name"]  # adjust per model if needed
    for field in required_fields:
        if not body.get(field):
            return response_switch(
                "missing",
                message=f"Please fill {field}",
                data=[],
                framework="fastapi"
            )

    try:
        validated_data = InputSchema(**body)
    except Exception as e:
        return response_switch("bad_request", message=f"Validation error: {e}", framework="fastapi")

    record_data = validated_data.dict(exclude_unset=True)
    record_data["created_by"] = user_id
    record_data["updated_by"] = user_id
    record_data["status"] = 1
    record_data["is_active"] = 1

    try:
        new_record = await model.create(**record_data)
    except Exception as e:
        return response_switch("bad_request", message=f"Error creating record: {e}", framework="fastapi")

    response_data = await OutputSchema.from_tortoise_orm(new_record)

    await manager.broadcast(model_name, {
        "event": f"{model_name}_created",
        "data": response_data.dict()
    })

    return response_switch(
        "created",
        message=f"{model_name} added successfully",
        data=response_data.dict(),
        framework="fastapi"
    )



@app.get("/api/{model_name}/list/")
async def list_records(
    model_name: str,
    user_id=Depends(get_current_user),
    pk: int = Query(None, description="Primary key to fetch a single record"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filters: str = Query("{}", description="JSON string of filters")
):
    serializers = get_model_and_serializers(model_name)
    if not serializers:
        return response_switch("not_found", message="Invalid model", framework="fastapi")

    model, out_pydantic, _ = serializers
    base_filters = {"status": 1}

    # If pk is provided, return single record
    if pk is not None:
        obj = await model.filter(id=pk, **base_filters).first()
        if not obj:
            return response_switch("not_found", message=f"Record with id {pk} not found", framework="fastapi")
        
        obj_out = await out_pydantic.from_tortoise_orm(obj)
        return response_switch(
            "success",
            message="Record retrieved successfully",
            data=serialize_data(obj_out.dict()),
            framework="fastapi"
        )

    # Parse filters JSON string
    try:
        filters_dict = json.loads(filters)
    except json.JSONDecodeError:
        return response_switch("bad_request", message="Invalid JSON for filters", framework="fastapi")

    # Merge with base filters
    filters_dict.update(base_filters)

    try:
        query = model.filter(**filters_dict)
    except Exception as e:
        return response_switch("bad_request", message=f"Invalid filter parameters: {e}", framework="fastapi")

    total = await query.count()
    query = query.offset((page - 1) * page_size).limit(page_size).order_by("-id")
    objs_out = await out_pydantic.from_queryset(query)
    objs_list = [obj.dict() for obj in objs_out]
    serialized_data = serialize_data(objs_list)

    return response_switch(
        "success",
        message="Records retrieved successfully",
        data={
            "results": serialized_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        },
        framework="fastapi"
    )


@app.put("/api/{model_name}/update/")
async def update_record(
    model_name: str,
    request: Request,
    pk: int = Query(..., description="Primary key of the record to update"),
    user_id=Depends(get_current_user)
):
    serializers = get_model_and_serializers(model_name)
    if not serializers:
        return response_switch("not_found", message="Invalid model", framework="fastapi")

    model, out_pydantic, in_pydantic = serializers

    obj = await model.get_or_none(pk=pk, status=1)
    if not obj:
        return response_switch("not_found", message="Record not found", framework="fastapi")

    data = await request.json()
    try:
        obj_in = in_pydantic(**data)
    except Exception as e:
        return response_switch("bad_request", message=f"Validation error: {e}", framework="fastapi")

    update_data = obj_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)

    obj.updated_by = user_id
    obj.updated_on = timezone.localtime(timezone.now())  # if you want to add updated_on timestamp

    await obj.save()

    obj_out = await out_pydantic.from_tortoise_orm(obj)

    await manager.broadcast(model_name, {
        "event": f"{model_name}_updated",
        "data": obj_out.dict()
    })

    return response_switch("success", message=f"{model_name} updated successfully", data=obj_out.dict(), framework="fastapi")



@app.patch("/api/{model_name}/delete/")
async def delete_record(
    model_name: str,
    pk: int = Query(...),
    user_id=Depends(get_current_user)
):
    serializers = get_model_and_serializers(model_name)
    if not serializers:
        return response_switch("not_found", message="Invalid model", framework="fastapi")

    model, out_pydantic, _ = serializers

    obj = await model.get_or_none(pk=pk, status=1)
    if not obj:
        return response_switch("not_found", message="Record not found or already deleted", framework="fastapi")

    obj.status = 0
    obj.updated_by = user_id
    obj.updated_on = timezone.localtime(timezone.now())  # optional

    await obj.save()

    obj_out = await out_pydantic.from_tortoise_orm(obj)

    await manager.broadcast(model_name, {
        "event": f"{model_name}_deleted",
        "data": obj_out.dict()
    })

    return response_switch("success", message=f"{model_name} deleted successfully", data=obj_out.dict(), framework="fastapi")


 
# ----------- WebSocket API -----------

@app.websocket("/api/{model_name}-ws/")
async def websocket_model_operations(model_name: str, websocket: WebSocket):
    await websocket.accept()

    serializers = get_model_and_serializers(model_name)
    if not serializers:
        await websocket.send_json({"error": "Invalid model name"})
        await websocket.close()
        return

    model, out_pydantic, in_pydantic = serializers
    await manager.connect(model_name, websocket)

    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")
            payload = message.get("data")

            if action == "add":
                try:
                    # Validate incoming data
                    obj_in = in_pydantic(**payload)
                except Exception as e:
                    await websocket.send_json({"error": str(e)})
                    continue
                
                obj_dict = obj_in.dict(exclude_unset=True)

                try:
                    # Use model instance + .save() to trigger overridden logic 
                    obj = model(**obj_dict)
                    await obj.save()  # This will call your custom save() with auto-generation

                    obj_out = await out_pydantic.from_tortoise_orm(obj)

                    await manager.broadcast(model_name, {
                        "event": f"{model_name}_created",
                        "data": obj_out.dict()
                    })

                except Exception as e:
                    await websocket.send_json({"error": str(e)})


            elif action == "list":
                try:
                    payload = payload or {}

                    page = payload.get("page", 1)
                    page_size = payload.get("page_size", 20)
                    filters = payload.get("filters", {})

                    # Add status=1 to filters to only get active records
                    filters["status"] = 1

                    query = model.filter(**filters) if filters else model.filter(status=1)

                    total = await query.count()
                    objs = await query.offset((page - 1) * page_size).limit(page_size).order_by("-id")
                    objs_out = [await out_pydantic.from_tortoise_orm(obj) for obj in objs]

                    await websocket.send_json({
                        "event": f"{model_name}_list",
                        "data": serialize_data([obj.dict() for obj in objs_out]),
                        "pagination": {
                            "page": page,
                            "page_size": page_size,
                            "total": total
                        }
                    })

                except Exception as e:
                    await websocket.send_json({"error": str(e)})


            elif action == "update":
                obj = await model.get_or_none(pk=payload.get("id"))
                if obj is None:
                    await websocket.send_json({"error": "Record not found"})
                    return
            
                try:
                    # Safely extract only valid input fields
                    existing_data = (await out_pydantic.from_tortoise_orm(obj)).dict()
                    allowed_fields = in_pydantic.model_fields.keys()
            
                    merged_data = {**{k: v for k, v in existing_data.items() if k in allowed_fields}, 
                                   **{k: v for k, v in payload.items() if k in allowed_fields}}
            
                    obj_in = in_pydantic(**merged_data)
                except Exception as e:
                    await websocket.send_json({"error": str(e)})
                    return
            
                obj_data = obj_in.dict(exclude_unset=True)
            
                for key, value in obj_data.items():
                    setattr(obj, key, value)
            
                await obj.save()
            
                obj_out = await out_pydantic.from_tortoise_orm(obj)
                await manager.broadcast(model_name, {
                    "event": f"{model_name}_updated",
                    "data": obj_out.dict()
                })
            

            elif action == "delete":
                obj = await model.get_or_none(pk=payload.get("id"))
                if obj is None:
                    await websocket.send_json({"error": "Record not found"})
                    continue
                
                try:
                    # Soft delete: set status = 0
                    obj.status = 0
                    await obj.save()

                    obj_out = await out_pydantic.from_tortoise_orm(obj)
                    await manager.broadcast(model_name, {
                        "event": f"{model_name}_deleted",  # or "_updated" if preferred
                        "data": obj_out.dict()
                    })

                except Exception as e:
                    await websocket.send_json({"error": str(e)})

            else:
                await websocket.send_json({"error": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        manager.disconnect(model_name, websocket)

