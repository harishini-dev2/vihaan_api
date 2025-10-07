from .views import * 

# Create your views here.

# -------------------------------------------------school-----------------------------------------------------------------------------------------

class SchoolAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id

            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            date_times = timezone.localtime(timezone.now())
           
            data = request.data.copy()

            # ✅ Check if school  name is provided
            name = data.get('name', '').strip()
            if not name:
                return response_switch(
                    "missing",
                    message="Please fill school name",
                    data=[]
                )
            
            data['created_on'] = date_times
            data['updated_by'] = employee_id
            data['created_by'] = employee_id
            data['updated_on'] = date_times
            data['status'] = 1
            data['is_active'] = 1


            serializer =SchoolSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return response_switch("success", message="school added successfully", data=serializer.data)
            else:
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while adding service", error=str(e))


class SchoolListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            school_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by school_id if provided
            if school_id and school_id.isdigit():
                query &= Q(id=school_id)

            # Search filter on school name, city, state
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
            school = selectList(school_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(school, request, view=self)

            serializer =SchoolSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="School list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )

class SchoolDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get school ID from query params
            school_id = request.query_params.get("id")
            if not school_id:
                return response_switch(
                    "missing",
                    message="School ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get authenticated employee
            auth_id = request.user.id
            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id

            # Filter school belonging to this user
            school = school_table.objects.filter(id=school_id, status=1, created_by=employee_id).first()

            if not school:
                return response_switch(
                    "not_found",
                    message="School not found",
                    error=f"No school found with id={school_id} for this user"
                )

            serializer = SchoolSerializer(school)
            return response_switch(
                "success",
                message="School retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving the school",
                error=str(e)
            )
        

        
class SchoolUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            school_id = request.query_params.get('id')
            if not school_id:
                return response_switch(
                    "missing",
                    message="School ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                school_table,
                id=school_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())

            # Serialize and update
            serializer =SchoolSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="School updated successfully",
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
        
class SchoolDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get school ID from query params
            school_id = request.query_params.get('id')

            if not school_id:
                return response_switch("missing", message="School ID is required", data=[])

            try:
                school_id_int = int(school_id)
            except ValueError:
                return response_switch("bad_request", message="School ID must be an integer", data=[])

            # Filter by active school created by this user
            school = school_table.objects.filter(id=school_id_int, status=1).first()

            if not school:
                return response_switch("not_found", message="School not found or already deleted")

            # Soft delete
            school.status = 0
            school.save()

            return response_switch("success", message=f"School deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the school", error=str(e))


