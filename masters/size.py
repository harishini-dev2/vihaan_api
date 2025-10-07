from .views import * 

# Create your views here.

# -------------------------------------------------size-----------------------------------------------------------------------------------------

class SizeAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id

            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            date_times = timezone.localtime(timezone.now())
           
            data = request.data.copy()

            # ✅ Check if size  name is provided
            name = data.get('name', '').strip()
            if not name:
                return response_switch(
                    "missing",
                    message="Please fill size name",
                    data=[]
                )
            
            data['created_on'] = date_times
            data['updated_by'] = employee_id
            data['created_by'] = employee_id
            data['updated_on'] = date_times
            data['status'] = 1
            data['is_active'] = 1


            serializer =SizeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return response_switch("success", message="size added successfully", data=serializer.data)
            else:
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while adding service", error=str(e))


class SizeListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            size_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by size_id if provided
            if size_id and size_id.isdigit():
                query &= Q(id=size_id)

            # Search filter on size name, city, state
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
            size = selectList(size_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(size, request, view=self)

            serializer =SizeSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="Size list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )

class SizeDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get size ID from query params
            size_id = request.query_params.get("id")
            if not size_id:
                return response_switch(
                    "missing",
                    message="Size ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter size belonging to this user
            size = size_table.objects.filter(id=size_id, status=1, created_by=employee_id).first()

            if not size:
                return response_switch(
                    "not_found",
                    message="Size not found",
                    error=f"No size found with id={size_id} for this user"
                )

            serializer = SizeSerializer(size)
            return response_switch(
                "success",
                message="Size retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the size",
                error=str(e)
            )


class SizeUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            size_id = request.query_params.get('id')
            if not size_id:
                return response_switch(
                    "missing",
                    message="Size ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                size_table,
                id=size_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())

            # Serialize and update
            serializer =SizeSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="Size updated successfully",
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
        
class SizeDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get size ID from query params
            size_id = request.query_params.get('id')

            if not size_id:
                return response_switch("missing", message="Size ID is required", data=[])

            try:
                size_id_int = int(size_id)
            except ValueError:
                return response_switch("bad_request", message="Size ID must be an integer", data=[])

            # Filter by active size created by this user
            size = size_table.objects.filter(id=size_id_int, status=1).first()

            if not size:
                return response_switch("not_found", message="Size not found or already deleted")

            # Soft delete
            size.status = 0
            size.save()

            return response_switch("success", message=f"Size deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the size", error=str(e))


