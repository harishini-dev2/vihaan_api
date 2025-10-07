from django.shortcuts import render
from common.utils import *
from .models import *
from websocket.models1 import *
from masters.serializers import *
from purchase_order.serializers import *
from common.views import * 
from django.db import transaction
from masters.models import *


class SchoolStyleList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            school_id = request.query_params.get('school_id')
            if not school_id:
                return response_switch(
                    "not_found",
                    message="School Id not found",
                    data=[]
                )

            styles = tm_style_table.objects.filter(
                school_id=school_id, status=1, is_active=1
            ).values("id", "name", "style_code")

            data = [
                {"id": s["id"], "name": f"{s['name']} ({s['style_code']})"} 
                for s in styles
            ]

            return response_switch(
                "success",
                message="Style list retrieved successfully",
                data=data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving styles",
                error=str(e)
            )


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from django.db.models import Q

class StyleDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            school_id = request.data.get('school_id')
            style_id = request.data.get('style_id')
            tm_id = request.data.get('tm_id')  #order tm_id

            if not school_id or not style_id:
                return response_switch(
                    "bad_request",
                    message="Missing school_id or style_id",
                    data={}
                )

            style = tm_style_table.objects.filter(
                status=1, school_id=school_id, id=style_id
            ).first()

            if not style:
                return response_switch(
                    "not_found",
                    message="Style not found for this school",
                    data={"colors": [], "sizes": [], "items": [], "position_size_map": {}}
                )

            # --- Colors ---
            color_ids = [int(c) for c in style.color_ids.split(',') if c.strip().isdigit()] if style.color_ids else []
            colors = list(color_table.objects.filter(
                status=1, is_active=1, id__in=color_ids
            ).values('id', 'name').order_by('id'))

            # --- Sizes & Positions ---
            tx_sizes = tx_style_table.objects.filter(
                style_id=style_id,
                status=1,
                is_active=1
            ).values('size_id', 'position').order_by('position')

            position_size_map = {}      # position -> size name
            position_size_id_map = {}   # position -> size id

            for ts in tx_sizes:
                size_obj = size_table.objects.filter(id=ts['size_id'], is_active=1, status=1).first()
                if size_obj:
                    position_size_map[ts['position']] = size_obj.name.strip().upper()
                    position_size_id_map[ts['position']] = size_obj.id

            # --- Existing items (for edit) ---
            items = []
            if tm_id:
                items = list(purchaseorder_item_table.objects.filter(
                    tm_order_id=tm_id, status=1, is_active=1
                ).values('size_id', 'color_id', 'quantity'))

            return response_switch(
                "success",
                message="Style details retrieved successfully",
                data={
                    "colors": colors,
                    "items": items,
                    "position_size_map": position_size_map,
                    "position_size_id_map": position_size_id_map
                }
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving style details",
                error=str(e)
            )



from rest_framework.exceptions import ValidationError

class PurchaseOrderAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            now = timezone.localtime(timezone.now())

            data = request.data.copy()
            items = data.pop("items", [])

            # Parse items if string (e.g., from form-data)
            if isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    return response_switch("bad_request", message="Invalid JSON in 'items'")

            # Validate required fields in items
            for index, item in enumerate(items):
                if "size_id" not in item or "quantity" not in item:
                    return response_switch(
                        "bad_request",
                        message=f"Missing 'size_id' or 'quantity' in item {index + 1}"
                    )

            # Set metadata for PO
            data.update({
                "created_by": employee_id,
                "updated_by": employee_id,
                "created_on": now,
                "updated_on": now,
                "po_date":now, 
                "is_active": 1,
                "status": 1,
            })
 
            po_serializer = PurchaseOrderSerializer(data=data)
            if po_serializer.is_valid():
                po_instance = po_serializer.save()

                for item in items:
                    item.update({
                        "po_id": po_instance.id,
                        "created_by": employee_id,
                        "updated_by": employee_id,
                        "created_on": now,
                        "updated_on": now,
                        "is_active": 1,
                        "status": 1,
                    })

                    item_serializer = PurchaseOrderItemSerializer(data=item)
                    if item_serializer.is_valid():
                        item_serializer.save()
                    else:
                        return response_switch(
                            "bad_request",
                            message="Validation error in one of the items",
                            error=item_serializer.errors
                        )

                full_data = PurchaseOrderSerializer(po_instance).data
                return response_switch(
                    "success",
                    message="Purchase Order created successfully with items",
                    data=full_data
                )

            else:
                return response_switch("bad_request", message="Validation error", error=po_serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Error creating purchase order", error=str(e))
        

from django.db.models import Q, Sum, OuterRef, Subquery, F, Case, When, Value, CharField, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.utils.dateparse import parse_date


class PurchaseOrderListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            search = request.query_params.get("search", "").strip()
            po_id = request.query_params.get("id")
            created_on = request.query_params.get("date")

            query = Q(status=1)

            if po_id and po_id.isdigit():
                query &= Q(id=po_id)

            if search:
                query &= (Q(po_number__icontains=search) | Q(po_name__icontains=search))

            if created_on:
                date_obj = parse_date(created_on)
                if not date_obj:
                    return response_switch("bad_request", message="Invalid date format (YYYY-MM-DD)")
                query &= Q(created_on__date=date_obj)

            delivery_sum = delivery_table.objects.filter(
                po_id=OuterRef('pk'), is_active=1, status=1
            ).values('po_id').annotate(total_qty=Sum('quantity')).values('total_qty')

            queryset = purchaseorder_table.objects.filter(query).annotate(
                total_delivered_quantity=Coalesce(Subquery(delivery_sum, output_field=DecimalField()), Decimal('0.00')),
            ).annotate(
                total_balance_quantity=ExpressionWrapper(
                    F('total_quantity') - F('total_delivered_quantity'),
                    output_field=DecimalField()
                ),
            ).annotate(
                po_status=Case(
                    When(total_balance_quantity__gt=Decimal('0.00'), then=Value('Pending')),
                    default=Value('Completed'),
                    output_field=CharField()
                )
            ).order_by("-created_on")

            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(queryset, request, view=self)

            serializer = PurchaseOrderSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch("success", message="Purchase orders listed successfully", data=response_data)

        except Exception as e:
            return response_switch("bad_request", message="Error fetching purchase orders", error=str(e))



class PurchaseOrderDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get purchaseorder ID from query params
            purchaseorder_id = request.query_params.get("id")
            if not purchaseorder_id:
                return response_switch(
                    "missing",
                    message="PurchaseOrder ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter purchaseorder belonging to this user
            purchaseorder = purchaseorder_table.objects.filter(id=purchaseorder_id, status=1, created_by=employee_id).first()

            if not purchaseorder:
                return response_switch(
                    "not_found",
                    message="PurchaseOrder not found",
                    error=f"No purchaseorder found with id={purchaseorder_id} for this user"
                )

            serializer = PurchaseOrderSerializer(purchaseorder)
            return response_switch(
                "success",
                message="PurchaseOrder retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the purchaseorder",
                error=str(e)
            )


class PurchaseOrderUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            tm_purchaseorder_id = request.query_params.get('id')
            if not tm_purchaseorder_id:
                return response_switch(
                    "missing",
                    message="PurchaseOrderTm ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                purchaseorder_table,
                id=tm_purchaseorder_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())
            data['updated_by']= request.user.id 
             
            # Prevent 'created_by' from being overwritten
            if 'created_by' in data: 
                data.pop('created_by')  
 
            # Serialize and update
            serializer =PurchaseOrderSerializer(instance, data=data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="PurchaseOrderTm updated successfully",
                    data=serializer.data
                )
            else:
                return response_switch(
                    "bad_request",
                    message="Validation error",
                    error=serializer.errors
                )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while updating service",
                error=str(e)
            )  
             
 

#------------------------------------------------------tm_order----------------------------------------------------------------------------------------------------------------

class PurchaseOrderDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get purchaseorder ID from query params
            purchaseorder_id = request.query_params.get('id')

            if not purchaseorder_id:
                return response_switch("missing", message="PurchaseOrder ID is required", data=[])

            try:
                purchaseorder_id_int = int(purchaseorder_id)
            except ValueError:
                return response_switch("bad_request", message="PurchaseOrder ID must be an integer", data=[])

            # Filter by active purchaseorder created by this user
            purchaseorder = purchaseorder_table.objects.filter(id=purchaseorder_id_int, status=1).first()

            if not purchaseorder:
                return response_switch("not_found", message="PurchaseOrder not found or already deleted")

            # Soft delete
            purchaseorder.status = 0
            purchaseorder.save()

            return response_switch("success", message=f"PurchaseOrder deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the purchaseorder", error=str(e))
        

#------------------------------------------------------tx_order----------------------------------------------------------------------------


class PurchaseOrderItemDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get purchaseorderitem ID from query params
            purchaseorderitem_id = request.query_params.get('id')

            if not purchaseorderitem_id:
                return response_switch("missing", message="PurchaseOrderItem ID is required", data=[])

            try:
                purchaseorderitem_id_int = int(purchaseorderitem_id)
            except ValueError:
                return response_switch("bad_request", message="PurchaseOrderItem ID must be an integer", data=[])

            # Filter by active purchaseorderitem created by this user
            purchaseorderitem = purchaseorder_item_table.objects.filter(id=purchaseorderitem_id_int, status=1).first()

            if not purchaseorderitem:
                return response_switch("not_found", message="PurchaseOrderItem not found or already deleted")

            # Soft delete
            purchaseorderitem.status = 0
            purchaseorderitem.save()

            return response_switch("success", message=f"PurchaseOrderItem deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the purchaseorderitem", error=str(e))


# class SavePurchaseOrderAPI(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             serializer = PurchaseOrderSerializer(data=request.data)
#             if serializer.is_valid():
#                 order = serializer.save()
#                 return Response({
#                     "message": "success",
#                     "order_id": order.id
#                 })
#             else:
#                 return Response({
#                     "message": "validation_error",
#                     "errors": serializer.errors
#                 }, status=400)
#         except Exception as e:
#             return Response({
#                 "message": "error",
#                 "error": str(e)
#             }, status=500)