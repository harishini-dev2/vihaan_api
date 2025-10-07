from .views import * 

# Create your views here.

# -------------------------------------------------category-----------------------------------------------------------------------------------------

class CategoryAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id

            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            date_times = timezone.localtime(timezone.now())
           
            data = request.data.copy()

            # ✅ Check if category  name is provided
            name = data.get('name', '').strip()
            if not name:
                return response_switch(
                    "missing",
                    message="Please fill category name",
                    data=[]
                )
            
            data['created_on'] = date_times
            data['updated_by'] = employee_id
            data['created_by'] = employee_id
            data['updated_on'] = date_times
            data['status'] = 1
            data['is_active'] = 1


            serializer =CategorySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return response_switch("success", message="category added successfully", data=serializer.data)
            else:
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while adding service", error=str(e))


class CategoryListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            category_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by category_id if provided
            if category_id and category_id.isdigit():
                query &= Q(id=category_id)

            # Search filter on category name, city, state
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
            category = selectList(category_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(category, request, view=self)

            serializer =CategorySerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="Category list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )
 

class CategoryDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get category ID from query params
            category_id = request.query_params.get("id")
            if not category_id:
                return response_switch(
                    "missing",
                    message="Category ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter category belonging to this user
            category = category_table.objects.filter(id=category_id, status=1, created_by=employee_id).first()

            if not category:
                return response_switch(
                    "not_found",
                    message="Category not found",
                    error=f"No category found with id={category_id} for this user"
                )

            serializer = CategorySerializer(category)
            return response_switch(
                "success",
                message="Category retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the category",
                error=str(e)
            )


class CategoryUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            category_id = request.query_params.get('id')
            if not category_id:
                return response_switch(
                    "missing",
                    message="Category ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                category_table,
                id=category_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())

            # Serialize and update
            serializer =CategorySerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="Category updated successfully",
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
        
class CategoryDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get category ID from query params
            category_id = request.query_params.get('id')

            if not category_id:
                return response_switch("missing", message="Category ID is required", data=[])

            try:
                category_id_int = int(category_id)
            except ValueError:
                return response_switch("bad_request", message="Category ID must be an integer", data=[])

            # Filter by active category created by this user
            category = category_table.objects.filter(id=category_id_int, status=1).first()

            if not category:
                return response_switch("not_found", message="Category not found or already deleted")

            # Soft delete
            category.status = 0
            category.save()

            return response_switch("success", message=f"Category deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the category", error=str(e))


