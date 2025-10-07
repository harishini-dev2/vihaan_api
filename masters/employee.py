from .views import * 

# Create your views here.

# -------------------------------------------------employee-----------------------------------------------------------------------------------------

class EmployeeAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id

            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            date_times = timezone.localtime(timezone.now())
           
            data = request.data.copy()

            # ✅ Check if employee  name is provided
            name = data.get('name', '').strip()
            if not name:
                return response_switch(
                    "missing",
                    message="Please fill employee name",
                    data=[]
                )
            
            data['created_on'] = date_times
            data['updated_by'] = employee_id
            data['created_by'] = employee_id
            data['updated_on'] = date_times
            data['status'] = 1
            data['is_active'] = 1


            serializer =EmployeeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return response_switch("success", message="employee added successfully", data=serializer.data)
            else:
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while adding service", error=str(e))


class EmployeeListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            employee_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by employee_id if provided
            if employee_id and employee_id.isdigit():
                query &= Q(id=employee_id)

            # Search filter on employee name, city, state
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
            employee = selectList(employee_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(employee, request, view=self)

            serializer =EmployeeSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="Employee list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )


class EmployeeDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get employee ID from query params
            employee_id = request.query_params.get("id")
            if not employee_id:
                return response_switch(
                    "missing",
                    message="Employee ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter employee belonging to this user
            employee = employee_table.objects.filter(id=employee_id, status=1, created_by=employee_id).first()

            if not employee:
                return response_switch(
                    "not_found",
                    message="Employee not found",
                    error=f"No employee found with id={employee_id} for this user"
                )

            serializer = EmployeeSerializer(employee)
            return response_switch(
                "success",
                message="Employee retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the employee",
                error=str(e)
            )

class EmployeeUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            employee_id = request.query_params.get('id')
            if not employee_id:
                return response_switch(
                    "missing",
                    message="Employee ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                employee_table,
                id=employee_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())

            # Serialize and update
            serializer =EmployeeSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="Employee updated successfully",
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
        
class EmployeeDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get employee ID from query params
            employee_id = request.query_params.get('id')

            if not employee_id:
                return response_switch("missing", message="Employee ID is required", data=[])

            try:
                employee_id_int = int(employee_id)
            except ValueError:
                return response_switch("bad_request", message="Employee ID must be an integer", data=[])

            # Filter by active employee created by this user
            employee = employee_table.objects.filter(id=employee_id_int, status=1).first()

            if not employee:
                return response_switch("not_found", message="Employee not found or already deleted")

            # Soft delete
            employee.status = 0
            employee.save()

            return response_switch("success", message=f"Employee deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the employee", error=str(e))


