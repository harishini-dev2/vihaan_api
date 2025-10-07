from .views import * 

# Create your views here.

# -------------------------------------------------packing-----------------------------------------------------------------------------------------

from django.db.models import Sum

from django.db.models import Sum

class PackingAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            now = timezone.localtime(timezone.now())

            data = request.data.copy()
            po_id = data.get("po_id")
            size_id = data.get("size_id")
            color_id = data.get("color_id")
            new_quantity = int(data.get("quantity", 0))

            if not all([po_id, size_id, color_id]):
                return response_switch("bad_request", message="po_id, size_id, and color_id are required.")

            # ✅ Get the specific PO item based on po_id, size_id, and color_id
            po_item = purchaseorder_item_table.objects.filter(
                po_id=po_id,
                size_id=size_id,
                color_id=color_id,
                is_active=1,
                status=1
            ).first()

            if not po_item:
                return response_switch("not_found", message="PO item not found for given size and color.")

            ordered_quantity = po_item.quantity or 0

            # ✅ Get total already packed for this exact po item
            already_packed_qty = packing_table.objects.filter(
                po_id=po_id,
                size_id=size_id,
                color_id=color_id,
                is_active=1,
                status=1
            ).aggregate(total_packed=Sum("quantity"))["total_packed"] or 0

            balance_quantity = ordered_quantity - already_packed_qty

            # ✅ Check packing limit
            if new_quantity > balance_quantity:
                return response_switch(
                    "invalid",
                    message=f"Cannot pack more than ordered. Ordered: {ordered_quantity}, Already packed: {already_packed_qty}, Balance: {balance_quantity}. You tried to pack: {new_quantity}"
                )

            # ✅ Add tracking info
            data['created_on'] = now
            data['updated_on'] = now
            data['created_by'] = employee_id
            data['updated_by'] = employee_id
            data['is_active'] = 1
            data['status'] = 1

            # ✅ Save
            serializer = PackingSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return response_switch("success", message="Packing added successfully", data=serializer.data)
            else:
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while adding packing", error=str(e))

# class PackingAddAPIView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             auth_id = request.user.id

#             employee = get_object_or_404(employee_table, auth_id=auth_id)
#             employee_id = employee.id
#             date_times = timezone.localtime(timezone.now())
           
#             data = request.data.copy()

#             # ✅ Check if packing  name is provided
#             # name = data.get('name', '').strip()
#             # if not name:
#             #     return response_switch(
#             #         "missing",
#             #         message="Please fill packing name",
#             #         data=[]
#             #     )
            
#             data['created_on'] = date_times 
#             data['updated_by'] = employee_id
#             data['created_by'] = employee_id
#             data['updated_on'] = date_times
#             data['status'] = 1
#             data['is_active'] = 1


#             serializer =PackingSerializer(data=data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return response_switch("success", message="packing added successfully", data=serializer.data)
#             else:
#                 return response_switch("bad_request", message="Validation error", error=serializer.errors)

#         except Exception as e:
#             return response_switch("bad_request", message="Something went wrong while adding service", error=str(e))


class PackingListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            packing_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by packing_id if provided
            if packing_id and packing_id.isdigit():
                query &= Q(id=packing_id)

            # Search filter on packing name, city, state
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
            packing = selectList(packing_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(packing, request, view=self)

            serializer =PackingSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="Packing list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )
 

class PackingDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get packing ID from query params
            packing_id = request.query_params.get("id")
            if not packing_id:
                return response_switch(
                    "missing",
                    message="Packing ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter packing belonging to this user
            packing = packing_table.objects.filter(id=packing_id, status=1, created_by=employee_id).first()

            if not packing:
                return response_switch(
                    "not_found",
                    message="Packing not found",
                    error=f"No packing found with id={packing_id} for this user"
                )

            serializer = PackingSerializer(packing)
            return response_switch(
                "success",
                message="Packing retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the packing",
                error=str(e)
            )



class PackingUpdateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            # ✅ Get ID from query param
            packing_id = request.query_params.get('id')
            if not packing_id:
                return response_switch(
                    "missing",
                    message="Packing ID is required in query parameters (?id=)",
                    data=[]
                )

            # ✅ Fetch existing packing record
            instance = get_object_or_404(packing_table, id=packing_id, status=1)

            # ✅ Extract new data
            data = request.data.copy()
            data['updated_on'] = timezone.localtime(timezone.now())

            # ✅ Check required fields for validation
            po_id = data.get("po_id", instance.po_id)
            size_id = data.get("size_id", instance.size_id)
            color_id = data.get("color_id", instance.color_id)
            new_quantity = int(data.get("quantity", instance.quantity))

            # ✅ Get the matching PO item
            po_item = purchaseorder_item_table.objects.filter(
                po_id=po_id,
                size_id=size_id,
                color_id=color_id,
                is_active=1,
                status=1
            ).first()

            if not po_item:
                return response_switch("not_found", message="PO item not found for size and color.")

            ordered_quantity = po_item.quantity or 0

            # ✅ Total already packed for this item (excluding current one)
            already_packed_qty = packing_table.objects.filter(
                po_id=po_id,
                size_id=size_id,
                color_id=color_id,
                is_active=1,
                status=1
            ).exclude(id=instance.id).aggregate(total_packed=Sum("quantity"))["total_packed"] or 0

            total_after_update = already_packed_qty + new_quantity

            if total_after_update > ordered_quantity:
                return response_switch(
                    "invalid",
                    message=(
                        f"Cannot update packing. Total after update ({total_after_update}) exceeds ordered quantity "
                        f"({ordered_quantity}). Already packed (excluding current): {already_packed_qty}, "
                        f"You're trying to update to: {new_quantity}"
                    )
                )

            # ✅ If valid, update the packing
            serializer = PackingSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="Packing updated successfully",
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
                message="Something went wrong while updating packing",
                error=str(e)
            )


# class PackingUpdateAPIView(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def put(self, request):
#         try:
           

#             # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
#             packing_id = request.query_params.get('id')
#             if not packing_id:
#                 return response_switch(
#                     "missing",
#                     message="Packing ID is required in query parameters (?id=)",
#                     data=[]
#                 )

#             # Get the brand only if created by the user
#             instance = get_object_or_404(
#                 packing_table,
#                 id=packing_id,
#                 status=1,
                
#             )

#             # Prepare update data
#             data = request.data.copy()
           
#             data['updated_on'] = timezone.localtime(timezone.now())

#             # Serialize and update
#             serializer =PackingSerializer(instance, data=data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return response_switch(
#                     "success",
#                     message="Packing updated successfully",
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
#                 message="Something went wrong while updating service",
#                 error=str(e)
#             )
        
class PackingDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get packing ID from query params
            packing_id = request.query_params.get('id')

            if not packing_id:
                return response_switch("missing", message="Packing ID is required", data=[])

            try:
                packing_id_int = int(packing_id)
            except ValueError:
                return response_switch("bad_request", message="Packing ID must be an integer", data=[])

            # Filter by active packing created by this user
            packing = packing_table.objects.filter(id=packing_id_int, status=1).first()

            if not packing:
                return response_switch("not_found", message="Packing not found or already deleted")

            # Soft delete
            packing.status = 0
            packing.save()

            return response_switch("success", message=f"Packing deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the packing", error=str(e))


