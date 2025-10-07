from .views import * 

# Create your views here.

# -------------------------------------------------financial_year-----------------------------------------------------------------------------------------

class FinancialYearAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_id = request.user.id

            employee = get_object_or_404(employee_table, auth_id=auth_id)
            employee_id = employee.id
            date_times = timezone.localtime(timezone.now())
           
            data = request.data.copy()

            # ✅ Check if financial_year  name is provided
            name = data.get('name', '').strip()
            if not name:
                return response_switch(
                    "missing",
                    message="Please fill financial_year name",
                    data=[]
                )
            
            data['created_on'] = date_times
            data['updated_by'] = employee_id
            data['created_by'] = employee_id
            data['updated_on'] = date_times
            data['status'] = 1
            data['is_active'] = 1


            serializer =FinancialYearSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return response_switch("success", message="financial_year added successfully", data=serializer.data)
            else:
                return response_switch("bad_request", message="Validation error", error=serializer.errors)

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while adding service", error=str(e))


class FinancialYearListAPIView(APIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Basic filters
            financial_year_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '').strip()
            created_on = request.query_params.get('date')  # expecting YYYY-MM-DD string

            # Start query with your required filters
            query = Q(status=1) 

            # Filter by financial_year_id if provided
            if financial_year_id and financial_year_id.isdigit():
                query &= Q(id=financial_year_id)

            # Search filter on financial_year name, city, state
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
            financial_year = selectList(financialyear_table, query)
            
            paginator = CustomPagination()
            paginated_qs = paginator.paginate_queryset(financial_year, request, view=self)

            serializer =FinancialYearSerializer(paginated_qs, many=True)

            response_data = {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data,
            }

            return response_switch(
                "success",
                message="FinancialYear list retrieved successfully",
                data=response_data
            )
        
        except Exception as e:
            return response_switch(
                "bad_request",
                message="Something went wrong while retrieving",
                error=str(e)
            )


class FinancialYearUpdate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
           

            # ✅ Get brand ID from query parameter (e.g. /brand-update/?id=5)
            financial_year_id = request.query_params.get('id')
            if not financial_year_id:
                return response_switch(
                    "missing",
                    message="FinancialYear ID is required in query parameters (?id=)",
                    data=[]
                )

            # Get the brand only if created by the user
            instance = get_object_or_404(
                financialyear_table,
                id=financial_year_id,
                status=1,
                
            )

            # Prepare update data
            data = request.data.copy()
           
            data['updated_on'] = timezone.localtime(timezone.now())

            # Serialize and update
            serializer =FinancialYearSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return response_switch(
                    "success",
                    message="FinancialYear updated successfully",
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
        
class FinancialYearDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
           

            # Get financial_year ID from query params
            financial_year_id = request.query_params.get('id')

            if not financial_year_id:
                return response_switch("missing", message="FinancialYear ID is required", data=[])

            try:
                financial_year_id_int = int(financial_year_id)
            except ValueError:
                return response_switch("bad_request", message="FinancialYear ID must be an integer", data=[])

            # Filter by active financial_year created by this user
            financial_year = financialyear_table.objects.filter(id=financial_year_id_int, status=1).first()

            if not financial_year:
                return response_switch("not_found", message="FinancialYear not found or already deleted")

            # Soft delete
            financial_year.status = 0
            financial_year.save()

            return response_switch("success", message=f"FinancialYear deleted successfully")

        except Exception as e:
            return response_switch("bad_request", message="Something went wrong while deleting the financial_year", error=str(e))


