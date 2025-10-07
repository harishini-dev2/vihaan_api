from .views import * 

# Create your views here.

# -------------------------------------------------style-----------------------------------------------------------------------------------------

class StyleAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            now = timezone.localtime(timezone.now())

            data = request.data.copy()
            size_items = data.pop("size_items", [])

            # If size_items is a string (e.g., from form-data), convert it
            if isinstance(size_items, str):
                try:
                    size_items = json.loads(size_items)
                except json.JSONDecodeError:
                    return response_switch("bad_request", message="Invalid JSON in size_items")

            data['created_on'] = now
            data['updated_by'] = employee_id
            data['created_by'] = employee_id
            data['updated_on'] = now
            data['status'] = 1
            data['is_active'] = 1

            tm_serializer = StyleTmSerializer(data=data)
            if tm_serializer.is_valid():
                tm_instance = tm_serializer.save()

                # ✅ Save related tx_style_table entries
                for size_item in size_items:
                    size_item['style_id'] = tm_instance.id
                    size_item['created_on'] = now
                    size_item['updated_on'] = now
                    size_item['created_by'] = employee_id
                    size_item['updated_by'] = employee_id
                    size_item['status'] = 1
                    size_item['is_active'] = 1

                    tx_serializer = StyleTxSerializer(data=size_item)
                    if tx_serializer.is_valid():
                        tx_serializer.save()
                    else:
                        return response_switch(
                            "bad_request",
                            message="Validation error in size_items",
                            error=tx_serializer.errors
                        )

                # ✅ Re-serialize with nested size_items included
                full_serializer = StyleTmSerializer(tm_instance)
                return response_switch(
                    "success",
                    message="StyleTm added with sizes successfully",
                    data=full_serializer.data
                )

            else:
                return response_switch(
                    "bad_request",
                    message="Validation error",
                    error=tm_serializer.errors
                )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while adding style",
                error=str(e)
            )



class StyleListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tm_style_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            query = Q(status=1)

            if tm_style_id and tm_style_id.isdigit():
                query &= Q(id=tm_style_id)

            if search_query:
                query &= (
                    Q(id__icontains=search_query) |
                    Q(name__icontains=search_query)
                )

            if created_on:
                try:
                    date_obj = parse_date(created_on)
                    query &= Q(created_on__date=date_obj.date())
                except Exception:
                    # Handle invalid date input gracefully
                    return response_switch(
                        "bad_request",
                        message="Invalid date format, expected YYYY-MM-DD",
                        error=None
                    )

            tm_style_qs = selectList(tm_style_table, query)

            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(tm_style_qs, request, view=self)

            serializer = StyleTmSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="StyleTm list retrieved successfully",
                data=response_data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )
        
class StyleUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            tm_style_id = request.query_params.get('id')
            if not tm_style_id:
                return response_switch(
                    "missing",
                    message="StyleTm ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                tm_style_table,
                id=tm_style_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())

            # Serialize and update
            serializer =StyleTmSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="StyleTm updated successfully",
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

# -------------------------------------------------tm_style-----------------------------------------------------------------------------------------

class StyleTmDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get tm_style ID from query params
            tm_style_id = request.query_params.get("id")
            if not tm_style_id:
                return response_switch(
                    "missing",
                    message="StyleTm ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter tm_style belonging to this user
            tm_style = tm_style_table.objects.filter(id=tm_style_id, status=1, created_by=employee_id).first()

            if not tm_style:
                return response_switch(
                    "not_found",
                    message="StyleTm not found",
                    error=f"No tm_style found with id={tm_style_id} for this user"
                )

            serializer = StyleTmSerializer(tm_style)
            return response_switch(
                "success",
                message="StyleTm retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the tm_style",
                error=str(e)
            )


        
class StyleTmDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get tm_style ID from query params
            tm_style_id = request.query_params.get('id')

            if not tm_style_id:
                return response_switch("missing", message="StyleTm ID is required", data=[])

            try:
                tm_style_id_int = int(tm_style_id)
            except ValueError:
                return response_switch("bad_request", message="StyleTm ID must be an integer", data=[])

            # Filter by active tm_style created by this user
            tm_style = tm_style_table.objects.filter(id=tm_style_id_int, status=1).first()

            if not tm_style:
                return response_switch("not_found", message="StyleTm not found or already deleted")

            # Soft delete
            tm_style.status = 0
            tm_style.save()

            return response_switch("success", message=f"StyleTm deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the tm_style", error=str(e))


# -------------------------------------------------tx_style-----------------------------------------------------------------------------------------



class StyleTxDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get tx_style ID from query params
            tx_style_id = request.query_params.get("id")
            if not tx_style_id:
                return response_switch(
                    "missing",
                    message="StyleTx ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter tx_style belonging to this user
            tx_style = tx_style_table.objects.filter(id=tx_style_id, status=1, created_by=employee_id).first()

            if not tx_style:
                return response_switch(
                    "not_found",
                    message="StyleTx not found",
                    error=f"No tx_style found with id={tx_style_id} for this user"
                )

            serializer = StyleTxSerializer(tx_style)
            return response_switch(
                "success",
                message="StyleTx retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the tx_style",
                error=str(e)
            )
        
      
class StyleTxDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:          

            # Get tx_style ID from query params
            tx_style_id = request.query_params.get('id')

            if not tx_style_id:
                return response_switch("missing", message="StyleTx ID is required", data=[])

            try:
                tx_style_id_int = int(tx_style_id)
            except ValueError:
                return response_switch("bad_request", message="StyleTx ID must be an integer", data=[])

            # Filter by active tx_style created by this user
            tx_style = tx_style_table.objects.filter(id=tx_style_id_int, status=1).first()

            if not tx_style:
                return response_switch("not_found", message="StyleTx not found or already deleted")

            # Soft delete
            tx_style.status = 0
            tx_style.save()

            return response_switch("success", message=f"StyleTx deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the tx_style", error=str(e))

