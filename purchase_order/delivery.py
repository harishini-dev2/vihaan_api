from .views import * 
from .box_packing import validate_quantity

# Create your views here.

# -------------------------------------------------delivery-----------------------------------------------------------------------------------------


class DeliveryAddAPIView(APIView):
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

            # Parse JSON if items is string (common in multipart requests)
            if isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    return response_switch("bad_request", message="Invalid JSON in 'items'")

            if not items:
                return response_switch("bad_request", message="Items list cannot be empty")

            # Extract po_id from first item's barcode (PO item barcode assumed)
            first_barcode = items[0].get("barcode")
            if not first_barcode:
                return response_switch("bad_request", message="First item barcode missing")
            
            # Look for box packing record by first barcode for delivery header
            boxpacking_first = boxpacking_table.objects.filter(barcode_str=first_barcode, status=1, is_active=1).first()
            if not boxpacking_first:
                return response_switch("bad_request", message=f"Invalid box packing barcode in first item: {first_barcode}")
            
            data["po_id"] = boxpacking_first.po_id  # use po_id from box packing for delivery header

            # Validate all items first before saving anything
            for idx, item in enumerate(items):
                barcode_str = item.get("barcode")
                quantity = item.get("quantity")

                if not barcode_str or quantity is None:
                    return response_switch("bad_request", message=f"Missing 'barcode' or 'quantity' in item {idx + 1}")

                # Validate quantity against packed quantity (using box_packing barcode validation)
                valid, msg = validate_quantity(
                    barcode_str=barcode_str,
                    new_quantity=quantity,
                    model=delivery_item_table,
                    barcode_type='box_packing'
                )
                if not valid:
                    return response_switch("invalid", message=f"Item {idx + 1} error: {msg}")

            # All validations passed, proceed to save
            data.update({
                "created_by": employee_id,
                "updated_by": employee_id,
                "created_on": now,
                "updated_on": now,
                "delivery_date": now,
                "is_active": 1,
                "status": 1
            })

            delivery_serializer = DeliverySerializer(data=data)
            if not delivery_serializer.is_valid():
                return response_switch("bad_request", message="Validation error", error=delivery_serializer.errors)

            delivery_instance = delivery_serializer.save()

            for idx, item in enumerate(items):
                barcode_str = item.get("barcode")
                boxpacking = boxpacking_table.objects.filter(barcode_str=barcode_str, status=1, is_active=1).first()
                if not boxpacking:
                    return response_switch("bad_request", message=f"Invalid box packing barcode in item {idx + 1}: {barcode_str}")

                delivery_item_table.objects.create(
                    delivery_id=delivery_instance.id,
                    box_packing_id=boxpacking.id,
                    barcode=boxpacking.barcode_str,
                    quantity=item.get("quantity"),
                    description=item.get("description", ""),
                    is_active=1,
                    status=1,
                    created_by=employee_id,
                    updated_by=employee_id,
                    created_on=now,
                    updated_on=now
                )

            full_data = DeliverySerializer(delivery_instance).data
            return response_switch("success", message="Delivery created successfully with items", data=full_data)

        except ValidationError as ve:
            return response_switch("failed", message=str(ve))
        except Exception as e:
            return response_switch("failed", message="Error creating delivery", error=str(e))

 
# class DeliveryAddAPIView(APIView):
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

#             # Parse JSON if items is string (common in multipart requests)
#             if isinstance(items, str):
#                 try:
#                     items = json.loads(items)
#                 except json.JSONDecodeError:
#                     return response_switch("bad_request", message="Invalid JSON in 'items'")

#             if not items:
#                 return response_switch("bad_request", message="Items list cannot be empty")

#             # Extract po_id from first item's barcode (you may adapt this logic)
#             first_barcode = items[0].get("barcode")
#             if not first_barcode:
#                 return response_switch("bad_request", message="First item barcode missing")

#             order_item = purchaseorder_item_table.objects.filter(barcode_str=first_barcode, status=1).first()
#             if not order_item:
#                 return response_switch("bad_request", message=f"Invalid barcode in first item: {first_barcode}")

#             data["po_id"] = order_item.po_id  # You might want to add po_id field to delivery_table if needed

#             # Add common fields
#             data.update({
#                 "created_by": employee_id,
#                 "updated_by": employee_id,
#                 "created_on": now,
#                 "updated_on": now,
#                 "delivery_date": now,
#                 "is_active": 1,
#                 "status": 1
#             })

#             # Create delivery
#             delivery_serializer = DeliverySerializer(data=data)
#             if not delivery_serializer.is_valid():
#                 return response_switch("bad_request", message="Validation error", error=delivery_serializer.errors)

#             delivery_instance = delivery_serializer.save()

#             # Save items
#             for idx, item in enumerate(items):
#                 barcode_str = item.get("barcode")
#                 quantity = item.get("quantity")
#                 description = item.get("description", "")

#                 if not barcode_str or quantity is None:
#                     return response_switch("bad_request", message=f"Missing 'barcode' or 'quantity' in item {idx + 1}")

#                 order_item = purchaseorder_item_table.objects.filter(barcode_str=barcode_str, status=1).first()
#                 if not order_item:
#                     return response_switch("bad_request", message=f"Invalid barcode '{barcode_str}' in item {idx + 1}")

#                 # You need to determine the correct box_packing_id or set it as 0 or None if not used
#                 delivery_item = delivery_item_table(
#                     delivery_id=delivery_instance.id,
#                     box_packing_id=0,  # Adjust this if you have actual box_packing id or remove field from model
#                     quantity=quantity,
#                     description=description,
#                     is_active=1,
#                     status=1,
#                     created_by=employee_id,
#                     updated_by=employee_id,
#                     created_on=now,
#                     updated_on=now
#                 )
#                 delivery_item.save()

#             full_data = DeliverySerializer(delivery_instance).data
#             return response_switch("success", message="Delivery created successfully with items", data=full_data)

#         except ValidationError as ve:
#             return response_switch("failed", message=str(ve))
#         except Exception as e:
#             return response_switch("failed", message="Error creating delivery", error=str(e))
 

class DeliveryListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            delivery_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD

            query = Q(status=1)

            if delivery_id and delivery_id.isdigit():
                query &= Q(id=delivery_id)

            if search_query:
                query &= (
                    Q(id__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

            if created_on:
                date_obj = parse_date(created_on)
                if date_obj:
                    query &= Q(created_on__date__gte=date_obj)

            deliveries = selectList(delivery_table, query)

            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(deliveries, request, view=self)

            serializer = DeliverySerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="Delivery list retrieved successfully",
                data=response_data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving deliveries",
                error=str(e)
            )


class DeliveryDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            delivery_id = request.query_params.get("id")
            if not delivery_id:
                return response_switch(
                    "missing",
                    message="Delivery ID is required in query parameters (?id=)",
                    data=[]
                )

            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            delivery = delivery_table.objects.filter(id=delivery_id, status=1, created_by=employee_id).first()

            if not delivery:
                return response_switch(
                    "not_found",
                    message="Delivery not found",
                    error=f"No delivery found with id={delivery_id} for this user"
                )

            serializer = DeliverySerializer(delivery)
            return response_switch(
                "success",
                message="Delivery retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the delivery",
                error=str(e)
            )

class DeliveryUpdateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            delivery_id = request.query_params.get('id')
            if not delivery_id:
                return response_switch(
                    "missing",
                    message="Delivery ID is required in query parameters (?id=)",
                    data=[]
                )

            instance = get_object_or_404(
                delivery_table,
                id=delivery_id,
                status=1,
            )

            data = request.data.copy()
            items = data.pop("items", None)

            # Parse items if string (common in multipart/form-data)
            if items and isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    return response_switch("bad_request", message="Invalid JSON in 'items'")

            # Validate all items before saving
            if items:
                for idx, item in enumerate(items):
                    barcode_str = item.get("barcode")
                    box_packing_id = item.get("box_packing_id")
                    quantity = item.get("quantity")

                    if quantity is None:
                        return response_switch(
                            "bad_request",
                            message=f"Missing 'quantity' in item {idx + 1}"
                        )

                    if not barcode_str and not box_packing_id:
                        return response_switch(
                            "bad_request",
                            message=f"Either 'barcode' or 'box_packing_id' must be provided in item {idx + 1}"
                        )

                    # Try to find existing delivery item by barcode or box_packing_id
                    if barcode_str:
                        delivery_item = delivery_item_table.objects.filter(
                            delivery_id=instance.id,
                            barcode=barcode_str,
                            status=1,
                            
                        ).first()
                    else:
                        delivery_item = delivery_item_table.objects.filter(
                            delivery_id=instance.id,
                            box_packing_id=box_packing_id,
                            status=1,
                            
                        ).first()

                    exclude_item_id = delivery_item.id if delivery_item else None

                    # For validation, determine barcode_str and barcode_type
                    if box_packing_id:
                        box = boxpacking_table.objects.filter(
                            id=box_packing_id,
                            status=1,
                            
                        ).first()
                        if not box:
                            return response_switch(
                                "invalid",
                                message=f"Invalid box_packing_id in item {idx + 1}"
                            )
                        validate_barcode = box.barcode_str
                        barcode_type = 'box_packing'
                    else:
                        validate_barcode = barcode_str
                        barcode_type = 'po_item'  # or 'box_packing', adjust as per your logic

                    valid, msg = validate_quantity(
                        barcode_str=validate_barcode,
                        new_quantity=quantity,
                        model=delivery_item_table,
                        barcode_type=barcode_type,
                        exclude_item_id=exclude_item_id
                    )

                    if not valid:
                        return response_switch("invalid", message=f"Item {idx + 1} error: {msg}")

            data['updated_on'] = timezone.localtime(timezone.now())

            serializer = DeliverySerializer(instance, data=data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()

                # Update or create delivery items if provided
                if items:
                    for item in items:
                        barcode_str = item.get("barcode")
                        box_packing_id = item.get("box_packing_id")
                        quantity = item.get("quantity")
                        description = item.get("description", "")

                        # Find existing delivery item by barcode or box_packing_id
                        if barcode_str:
                            delivery_item = delivery_item_table.objects.filter(
                                delivery_id=instance.id,
                                barcode=barcode_str,
                                status=1,
                                is_active=1
                            ).first()
                        elif box_packing_id:
                            delivery_item = delivery_item_table.objects.filter(
                                delivery_id=instance.id,
                                box_packing_id=box_packing_id,
                                status=1,
                                is_active=1
                            ).first()
                        else:
                            delivery_item = None

                        # Get box_packing_id if only barcode provided
                        if not box_packing_id and barcode_str:
                            box = boxpacking_table.objects.filter(
                                barcode_str=barcode_str,
                                status=1,
                                is_active=1
                            ).first()
                            box_packing_id = box.id if box else 0

                        if delivery_item:
                            delivery_item.quantity = quantity
                            delivery_item.description = description
                            delivery_item.box_packing_id = box_packing_id or delivery_item.box_packing_id
                            delivery_item.barcode = barcode_str or delivery_item.barcode
                            delivery_item.updated_on = timezone.localtime(timezone.now())
                            delivery_item.save()
                        else:
                            delivery_item_table.objects.create(
                                delivery_id=instance.id,
                                barcode=barcode_str or "",
                                box_packing_id=box_packing_id or 0,
                                quantity=quantity,
                                description=description,
                                is_active=1,
                                status=1,
                                created_by=instance.updated_by,
                                updated_by=instance.updated_by,
                                created_on=timezone.localtime(timezone.now()),
                                updated_on=timezone.localtime(timezone.now())
                            )

                return response_switch(
                    "success",
                    message="Delivery updated successfully",
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
                message="Something went wrong while updating delivery",
                error=str(e)
            )


 
# class DeliveryUpdateAPIView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def put(self, request):
#         try:
#             delivery_id = request.query_params.get('id')
#             if not delivery_id:
#                 return response_switch(
#                     "missing",
#                     message="Delivery ID is required in query parameters (?id=)",
#                     data=[]
#                 )

#             instance = get_object_or_404(
#                 delivery_table,
#                 id=delivery_id,
#                 status=1,
#             )

#             data = request.data.copy()
#             data['updated_on'] = timezone.localtime(timezone.now())

#             serializer = DeliverySerializer(instance, data=data, partial=True, context={'request': request})
#             if serializer.is_valid():
#                 serializer.save()
#                 return response_switch(
#                     "success",
#                     message="Delivery updated successfully",
#                     data=serializer.data
#                 )
#             else:
#                 return response_switch(
#                     "bad_request",
#                     message="Validation error",
#                     error=serializer.errors
#                 )

#         except Exception as e:
#             return response_switch(
#                 "bad_request",
#                 message="Something went wrong while updating delivery",
#                 error=str(e)
#             )


# ------------------------------------------------------------tm delivery -------------------------------------------------------------------------------------------------
class DeliveryTmDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            delivery_id = request.query_params.get('id')

            if not delivery_id:
                return response_switch("missing", message="Delivery ID is required", data=[])

            try:
                delivery_id_int = int(delivery_id)
            except ValueError:
                return response_switch("bad_request", message="Delivery ID must be an integer", data=[])

            delivery = delivery_table.objects.filter(id=delivery_id_int, status=1).first()

            if not delivery:
                return response_switch("not_found", message="Delivery not found or already deleted")

            # Soft delete
            delivery.status = 0
            delivery.save()

            return response_switch("success", message="Delivery deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the delivery", error=str(e))
        
# ------------------------------------------------------------tx delivery -------------------------------------------------------------------------------------------------


class DeliveryTxDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            delivery_id = request.query_params.get('id')

            if not delivery_id:
                return response_switch("missing", message="Delivery Item ID is required", data=[])

            try:
                delivery_id_int = int(delivery_id)
            except ValueError:
                return response_switch("bad_request", message="Delivery Item  ID must be an integer", data=[])

            delivery = delivery_item_table.objects.filter(id=delivery_id_int, status=1).first()

            if not delivery:
                return response_switch("not_found", message="Delivery Item not found or already deleted")

            # Soft delete
            delivery.status = 0
            delivery.save()

            return response_switch("success", message="Delivery Item deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the delivery item", error=str(e)) 
