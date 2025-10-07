from .views import * 

# Create your views here.

# -------------------------------------------------color-----------------------------------------------------------------------------------------

class ColorAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id

            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            date_times = timezone.localtime(timezone.now())
           
            data = request.data.copy()

            # ✅ Check if color  name is provided
            name = data.get('name', '').strip()
            if not name:
                return response_switch(
                    "missing",
                    message="Please fill color name",
                    data=[]
                )
            
            data['created_on'] = date_times
            data['updated_by'] = employee_id
            data['created_by'] = employee_id
            data['updated_on'] = date_times
            data['status'] = 1
            data['is_active'] = 1


            serializer =ColorSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return response_switch("success", message="color added successfully", data=serializer.data)
            else:
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while adding service", error=str(e))


class ColorListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            color_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by color_id if provided
            if color_id and color_id.isdigit():
                query &= Q(id=color_id)

            # Search filter on color name, city, state
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
            color = selectList(color_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(color, request, view=self)

            serializer =ColorSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="Color list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )
 

class ColorDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get color ID from query params
            color_id = request.query_params.get("id")
            if not color_id:
                return response_switch(
                    "missing",
                    message="Color ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter color belonging to this user
            color = color_table.objects.filter(id=color_id, status=1, created_by=employee_id).first()

            if not color:
                return response_switch(
                    "not_found",
                    message="Color not found",
                    error=f"No color found with id={color_id} for this user"
                )

            serializer = ColorSerializer(color)
            return response_switch(
                "success",
                message="Color retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the color",
                error=str(e)
            )


class ColorUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            color_id = request.query_params.get('id')
            if not color_id:
                return response_switch(
                    "missing",
                    message="Color ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                color_table,
                id=color_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())

            # Serialize and update
            serializer =ColorSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="Color updated successfully",
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
        
class ColorDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get color ID from query params
            color_id = request.query_params.get('id')

            if not color_id:
                return response_switch("missing", message="Color ID is required", data=[])

            try:
                color_id_int = int(color_id)
            except ValueError:
                return response_switch("bad_request", message="Color ID must be an integer", data=[])

            # Filter by active color created by this user
            color = color_table.objects.filter(id=color_id_int, status=1).first()

            if not color:
                return response_switch("not_found", message="Color not found or already deleted")

            # Soft delete
            color.status = 0
            color.save()

            return response_switch("success", message=f"Color deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the color", error=str(e))


