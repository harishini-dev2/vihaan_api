from .views import * 

# Create your views here.

# -------------------------------------------------boxpacking-----------------------------------------------------------------------------------------


class PoNumberList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            school_id = request.query_params.get('school_id')
            style_id = request.query_params.get('style_id') 
            category_id = request.query_params.get('category_id')

            # Validate both parameters
            if not school_id:
                return response_switch(
                    "not_found",
                    message="School Id not found",
                    data=[]
                )

            if not style_id:
                return response_switch(
                    "not_found",
                    message="Style Id not found",
                    data=[]
                )
            
            if not category_id:
                return response_switch(
                    "not_found",
                    message="Category Id not found",
                    data=[]
                )

            # Fetch styles filtered by school_id and category_id
            po_number = purchaseorder_table.objects.filter(
                school_id=school_id,
                style_id=style_id,
                category_id= category_id,
                status=1,
                is_active=1
            ).values("id", "po_number")

            # Format the response data
            data = [
                {"id": s["id"], "po": f"{s['po_number']} "} 
                for s in po_number
            ]

            return response_switch(
                "success",
                message="Po Number list retrieved successfully",
                data=data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving Po Number",
                error=str(e)
            )


# class BoxPackingAddAPIView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             auth_id = request.user.id
#             employee = get_object_or_404(employee_table, auth_id=auth_id)
#             employee_id = employee.id
#             now = timezone.localtime(timezone.now())

#             data = request.data.copy()
#             items = data.pop("items", [])

#             # If items is a string (e.g. from multipart/form-data), parse JSON
#             if isinstance(items, str):
#                 try:
#                     items = json.loads(items)
#                 except json.JSONDecodeError:
#                     return response_switch("bad_request", message="Invalid JSON in 'items'")

#             if not items:
#                 return response_switch("bad_request", message="Items list cannot be empty")

#             # Set po_id from first valid item's barcode
#             first_barcode = items[0].get("barcode")
#             if not first_barcode:
#                 return response_switch("bad_request", message="First item barcode missing")

#             order_item = purchaseorder_item_table.objects.filter(barcode_str=first_barcode, status=1).first()
#             if not order_item:
#                 return response_switch("bad_request", message=f"Invalid barcode in first item: {first_barcode}")

#             data["po_id"] = order_item.po_id

#             # Add common fields
#             data.update({
#                 "created_by": employee_id,
#                 "updated_by": employee_id,
#                 "created_on": now,
#                 "updated_on": now,
#                 "box_date" : now, 
#                 "is_active": 1,
#                 "status": 1
#             })

#             # Validate and save box packing header
#             box_serializer = BoxPackingSerializer(data=data)
#             if not box_serializer.is_valid():
#                 return response_switch("bad_request", message="Validation error", error=box_serializer.errors)

#             box_instance = box_serializer.save()

#             # Save each item
#             for index, item in enumerate(items):
#                 barcode_str = item.get("barcode")
#                 quantity = item.get("quantity")

#                 if not barcode_str or quantity is None:
#                     return response_switch(
#                         "bad_request",
#                         message=f"Missing 'barcode' or 'quantity' in item {index + 1}"
#                     )

#                 order_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_str, status=1).first()
#                 if not order_item:
#                     return response_switch(
#                         "bad_request",
#                         message=f"Invalid barcode '{barcode_str}' in item {index + 1}"
#                     )

#                 box_item = boxpacking_item_table(
#                     box_packing_id=box_instance.id,
#                     po_id=order_item.po_id,
#                     barcode=barcode_str,
#                     quantity=quantity,
#                     description=item.get("description", ""),
#                     is_active=1,
#                     status=1,
#                     created_by=employee_id,
#                     updated_by=employee_id,
#                     created_on=now,
#                     updated_on=now
#                 )
#                 box_item.save()

#             # Return the saved data
#             full_data = BoxPackingSerializer(box_instance).data
#             return response_switch("success", message="Box Packing created successfully with items", data=full_data)

#         except ValidationError as ve:
#             return response_switch("failed", message=str(ve))
#         except Exception as e:
#             return response_switch("failed", message="Error creating box packing", error=str(e))
 

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
from django.utils import timezone

# Reusable quantity validation helper
from django.db.models import Sum

def validate_quantity(
    barcode_str,
    new_quantity,
    model,
    barcode_type='po_item',
    box_packing_id=None,
    exclude_item_id=None
):
    """
    Validate quantity against PO ordered quantity or box packed quantity.

    :param barcode_str: Barcode string (PO item barcode or box packing barcode)
    :param new_quantity: The quantity being added or updated
    :param model: Django model to validate against (e.g. packing_table or delivery_item_table)
    :param barcode_type: 'po_item' to validate packing against PO, 'box_packing' to validate delivery against box
    :param box_packing_id: (Only for 'po_item') Exclude this box_packing_id during update
    :param exclude_item_id: (Only for 'box_packing') Exclude this delivery item ID during update
    :return: (bool, error_message or None)
    """

    # ------------------------
    # Case 1: Packing against PO item
    # ------------------------
    if barcode_type == 'po_item':
        po_item = purchaseorder_item_table.objects.filter(
            barcode_str=barcode_str,
            status=1,
            is_active=1
        ).first()

        if not po_item:
            return False, f"Invalid PO item barcode: {barcode_str}"

        ordered_qty = po_item.quantity or 0

        # Sum already packed quantity excluding current box if updating
        queryset = model.objects.filter(
            po_id=po_item.po_id,
            status=1,
            is_active=1
        )

        if box_packing_id:
            queryset = queryset.exclude(box_packing_id=box_packing_id)

        already_used_qty = queryset.aggregate(total=Sum('quantity'))['total'] or 0
        balance_qty = ordered_qty - already_used_qty

        if new_quantity > balance_qty:
            return False, (
                f"Exceeds ordered quantity. "
                f"Ordered: {ordered_qty}, Already used: {already_used_qty}, "
                f"Trying to add/update: {new_quantity}"
            )

        return True, None

    # ------------------------
    # Case 2: Delivering from Box Packing
    # ------------------------
    elif barcode_type == 'box_packing':
        box = boxpacking_table.objects.filter(
            barcode_str=barcode_str,
            status=1,
            is_active=1
        ).first()

        if not box:
            return False, f"Invalid box packing barcode: {barcode_str}"

        # Total packed quantity inside the box
        packed_qty = boxpacking_item_table.objects.filter(
            box_packing_id=box.id,
            status=1,
            is_active=1
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # Total quantity already delivered from this box, excluding current delivery item if updating
        queryset = model.objects.filter(
            box_packing_id=box.id,
            status=1,
            is_active=1
        )

        if exclude_item_id:
            queryset = queryset.exclude(id=exclude_item_id)

        already_delivered_qty = queryset.aggregate(total=Sum('quantity'))['total'] or 0
        balance_qty = packed_qty - already_delivered_qty

        if new_quantity > balance_qty:
            return False, (
                f"Exceeds packed quantity for box '{box.box_number}'. "
                f"Packed: {packed_qty}, Already delivered: {already_delivered_qty}, "
                f"Trying to add/update: {new_quantity}"
            )

        return True, None

    # ------------------------
    # Unknown Barcode Type
    # ------------------------
    else:
        return False, "Unknown barcode_type specified. Must be 'po_item' or 'box_packing'."



class BoxPackingAddAPIView(APIView):
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

            # Parse JSON string if necessary
            if isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    return response_switch("bad_request", message="Invalid JSON in 'items'")

            if not items:
                return response_switch("bad_request", message="Items list cannot be empty")

            # Validate po_id using first item's barcode
            first_barcode = items[0].get("barcode")
            if not first_barcode:
                return response_switch("bad_request", message="First item barcode missing")

            order_item = purchaseorder_item_table.objects.filter(barcode_str=first_barcode, status=1, is_active=1).first()
            if not order_item:
                return response_switch("bad_request", message=f"Invalid barcode in first item: {first_barcode}")

            data["po_id"] = order_item.po_id

            # Phase 1: Validate all items before saving anything
            for idx, item in enumerate(items):
                barcode_str = item.get("barcode")
                quantity = item.get("quantity")

                if not barcode_str or quantity is None:
                    return response_switch("bad_request", message=f"Missing 'barcode' or 'quantity' in item {idx + 1}")

                order_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_str, status=1, is_active=1).first()
                if not order_item:
                    return response_switch("bad_request", message=f"Invalid barcode '{barcode_str}' in item {idx + 1}")
                
                valid, msg = validate_quantity(
                    barcode_str=barcode_str,
                    new_quantity=quantity,
                    model=packing_table,
                    barcode_type='po_item'
                )
                if not valid:
                    return response_switch("invalid", message=msg)


            # Phase 2: All validations passed, now save data

            # Add audit/status fields
            data.update({
                "created_by": employee_id,
                "updated_by": employee_id,
                "created_on": now,
                "updated_on": now,
                "box_date": now,
                "is_active": 1,
                "status": 1
            })

            box_serializer = BoxPackingSerializer(data=data)
            if not box_serializer.is_valid():
                return response_switch("bad_request", message="Validation error", error=box_serializer.errors)

            box_instance = box_serializer.save()

            # Save all items
            for item in items:
                barcode_str = item.get("barcode")
                quantity = item.get("quantity")
                description = item.get("description", "")

                order_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_str, status=1, is_active=1).first()

                box_item = boxpacking_item_table(
                    box_packing_id=box_instance.id,
                    po_id=order_item.po_id,
                    barcode=barcode_str,
                    quantity=quantity,
                    description=description,
                    is_active=1,
                    status=1,
                    created_by=employee_id,
                    updated_by=employee_id,
                    created_on=now,
                    updated_on=now
                )
                box_item.save()

            full_data = BoxPackingSerializer(box_instance).data
            return response_switch("success", message="Box Packing created successfully with items", data=full_data)

        except ValidationError as ve:
            return response_switch("failed", message=str(ve))
        except Exception as e:
            return response_switch("failed", message="Error creating box packing", error=str(e))
 


class BoxPackingListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            boxpacking_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by boxpacking_id if provided
            if boxpacking_id and boxpacking_id.isdigit():
                query &= Q(id=boxpacking_id)

            # Search filter on boxpacking name, city, state
            if search_query:
                query &= (
                    Q(id__icontains=search_query) |
                    Q(name__icontains=search_query) 
                )

            # Search filter on date
            if created_on:
                date_obj = parse_date(created_on)
                if date_obj:
                    query &= Q(created_on__date__gte=date_obj)


            # Use your selectList to get queryset with filters
            boxpacking = selectList(boxpacking_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(boxpacking, request, view=self)

            serializer =BoxPackingSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="BoxPacking list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )
 

class BoxPackingDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get boxpacking ID from query params
            boxpacking_id = request.query_params.get("id")
            if not boxpacking_id:
                return response_switch(
                    "missing",
                    message="BoxPacking ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter boxpacking belonging to this user
            boxpacking = boxpacking_table.objects.filter(id=boxpacking_id, status=1, created_by=employee_id).first()

            if not boxpacking:
                return response_switch(
                    "not_found",
                    message="BoxPacking not found",
                    error=f"No boxpacking found with id={boxpacking_id} for this user"
                )

            serializer = BoxPackingSerializer(boxpacking)
            return response_switch(
                "success",
                message="BoxPacking retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the boxpacking",
                error=str(e)
            )

class BoxPackingUpdateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            boxpacking_id = request.query_params.get('id')
            if not boxpacking_id:
                return response_switch(
                    "missing",
                    message="BoxPacking ID is required in query parameters (?id=)",
                    data=[]
                )

            instance = get_object_or_404(boxpacking_table, id=boxpacking_id, status=1)

            data = request.data.copy()
            items = data.pop("items", None)  # Optional items list for update

            data['updated_on'] = timezone.localtime(timezone.now())

            # Validate items first if items provided
            if items is not None:
                if isinstance(items, str):
                    try:
                        items = json.loads(items)
                    except json.JSONDecodeError:
                        return response_switch("bad_request", message="Invalid JSON in 'items'")

                if not items:
                    return response_switch("bad_request", message="Items list cannot be empty")

                for idx, item in enumerate(items):
                    barcode_str = item.get("barcode")
                    quantity = item.get("quantity")

                    if not barcode_str or quantity is None:
                        return response_switch("bad_request", message=f"Missing 'barcode' or 'quantity' in item {idx + 1}")

                    order_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_str, status=1, is_active=1).first()
                    if not order_item:
                        return response_switch("bad_request", message=f"Invalid barcode '{barcode_str}' in item {idx + 1}")

                    valid, error_msg = validate_quantity(
                        barcode_str=barcode_str,
                        new_quantity=quantity,
                        model=boxpacking_item_table,
                        box_packing_id=boxpacking_id, # exclude current record quantities during validation
                        barcode_type='po_item'  
                    )
                    if not valid:
                        return response_switch("invalid", message=error_msg)

            # Update box packing header
            serializer = BoxPackingSerializer(instance, data=data, partial=True, context={'request': request})
            if not serializer.is_valid():
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

            box_instance = serializer.save()

            if items is not None:
                # Delete old items related to this boxpacking
                boxpacking_item_table.objects.filter(box_packing_id=boxpacking_id).delete()

                now = timezone.localtime(timezone.now())
                employee_id = request.user.id  # or fetch employee id properly if needed

                # Save new items
                for item in items:
                    barcode_str = item.get("barcode")
                    quantity = item.get("quantity")
                    description = item.get("description", "")

                    order_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_str, status=1, is_active=1).first()

                    box_item = boxpacking_item_table(
                        box_packing_id=box_instance.id,
                        po_id=order_item.po_id,
                        barcode=barcode_str,
                        quantity=quantity,
                        description=description,
                        is_active=1,
                        status=1,
                        created_by=employee_id,
                        updated_by=employee_id,
                        created_on=now,
                        updated_on=now
                    )
                    box_item.save()

            full_data = BoxPackingSerializer(box_instance).data
            return response_switch("success", message="BoxPacking updated successfully", data=full_data)

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while updating Box Packing",
                error=str(e)
            )


# ----------------------------------------tm box packing-----------------------------------------------------------------------------------------------------------------


class BoxPackingTmDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           
            # Get boxpacking ID from query params
            boxpacking_id = request.query_params.get('id')

            if not boxpacking_id:
                return response_switch("missing", message="BoxPacking ID is required", data=[])

            try:
                boxpacking_id_int = int(boxpacking_id)
            except ValueError:
                return response_switch("bad_request", message="BoxPacking ID must be an integer", data=[])

            # Filter by active boxpacking created by this user
            boxpacking = boxpacking_table.objects.filter(id=boxpacking_id_int, status=1).first()      

            if not boxpacking:
                return response_switch("not_found", message="BoxPacking not found or already deleted")

            # Soft delete
            boxpacking.status = 0
            boxpacking.save()

            return response_switch("success", message=f"BoxPacking deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the boxpacking", error=str(e))

# ----------------------------------------tx box packing-----------------------------------------------------------------------------------------------------------------

class BoxPackingTxDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           
            # Get boxpacking ID from query params
            boxpacking_id = request.query_params.get('id')

            if not boxpacking_id:
                return response_switch("missing", message="Box Packing Item ID is required", data=[])

            try:
                boxpacking_id_int = int(boxpacking_id)
            except ValueError:
                return response_switch("bad_request", message="Box Packing Item ID must be an integer", data=[])

            # Filter by active boxpacking created by this user
            boxpacking = boxpacking_item_table.objects.filter(id=boxpacking_id_int, status=1).first()      

            if not boxpacking:
                return response_switch("not_found", message="Box Packing Item not found or already deleted")

            # Soft delete
            boxpacking.status = 0
            boxpacking.save()

            return response_switch("success", message=f"Box Packing Item deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the boxpacking item", error=str(e)) 