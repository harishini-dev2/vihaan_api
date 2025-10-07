from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.http import JsonResponse
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from common.models import *
from django.db.models import Max
from django.db.models import Max, F, Q
import base64
from datetime import datetime
from django.utils import timezone

# *************************************************************************************************************************

def week_of_month(dt):        
    first_day = dt.replace(day=1)
    dom = dt.day
    adjusted_dom = dom + first_day.weekday()
    return int((adjusted_dom - 1) / 7) + 1

# **************************************************************************************************************************
# DATE FORMAT
# ***********


# Format datetim
def format_datetime(date):
    return date.strftime('%Y-%m-%d %H:%M:%S') if date else None


# Format Date
def format_date(date):
    return date.strftime('%Y-%m-%d') if date else None

# Format Time
def format_time(date):
    return date.strftime('%H:%M:%S') if date else None


# Format Time(Hours Minute)
def format_hr_m(date):
    return date.strftime('%H:%M') if date else None


# Format Date (D:M:Y)
def format_date_month_year(date):
    if not date:
        return None
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    return date.strftime('%d-%m-%Y')


# Control Date if pausing null
def normalize_date(date_str):    
    if not date_str or date_str in ["0000-00-00", "0000-00-00 00:00:00"]:
        return None
    return date_str


# Convert the date into Y:M:D format
def parse_date(date_str):
    """
    Tries to parse various common date formats and convert to YYYY-MM-DD.
    Returns None if parsing fails.
    """
    if not date_str:
        return None

    date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None  # If no format matched



# **************************************************************************************************************************
# Format amount with .00
def format_amount(value):
    try:
        if value is None:
            return '-'
        return "{:.2f}".format(float(value))
    except (ValueError, TypeError): 
        return '-'


# **************************************************************************************************************************


# get name against id
def getItemNameById(tbl, cat_id):
    try:
        category = tbl.objects.get(id=cat_id).name
        return category
    except tbl.DoesNotExist:
        return '-' 
    except Exception as e:
        return '-' 
    
# Get Id by name
def getItemIdByName(tbl, name):
    try:
        return tbl.objects.get(name=name).id
    except tbl.DoesNotExist:
        return 0
    except Exception:
        return 0
    

# **************************************************************************************************************************

#select a single row based on table and where condition


def selectList(tbl, whr=None, order_by='-id', status_filter=True, fields=None):
    """
    Fetch multiple rows from the table `tbl` based on the condition `whr` (can be dict or Q object),
    and optional `order_by` argument. Always includes condition status=1 by default.
    category = selectList(category_table, {'some_field': some_value}, order_by='name')

    """
    query = Q(status=1) if status_filter else Q()

    if whr:
        if isinstance(whr, dict):
            query &= Q(**whr)
        elif isinstance(whr, Q):
            query &= whr
        else:
            raise ValueError("Invalid 'whr' argument. Must be dict, Q object, or None.")

    queryset = tbl.objects.filter(query).order_by(order_by)
    
    if fields:
        return queryset.values(*fields)
    
    return queryset



def select_row(tbl, whr=None):
    """
    Fetch a single row from the given table `tbl` with the condition `whr`.
    Always includes condition status=1 by default.
    """
    query = Q(status=1)

    if whr is not None:
        if isinstance(whr, dict):
            query &= Q(**whr)
        elif isinstance(whr, Q):
            query &= whr
        else:
            raise ValueError("Invalid 'whr' argument. Must be dict, Q object, or None.")

    return tbl.objects.filter(query).first()


# **************************************************************************************************************************

# Convert comma separated as single id
def comma_separated(id_string):
    """
    Convert a comma-separated string into a list of integers.
    Handles empty strings and strips whitespace.
    """
    if not id_string:
        return []
    return [int(i.strip()) for i in id_string.split(',') if i.strip().isdigit()]



def has_negative_values(data, fields):
    """
    Checks if any given field in `data` has a negative value.
    `data` is a dictionary (e.g., request.POST).
    """
    for field in fields:
        try:
            value = float(data.get(field, 0))
            if value < 0:
                return True, f"{field.replace('_', ' ').title()} cannot be negative."
        except (ValueError, TypeError):
            continue
    return False, ""

# **************************************************************************************************************************

from rest_framework import viewsets, status
from rest_framework.response import Response


def build_response(
    message="",
    data=None,
    status_code=status.HTTP_200_OK,
    response_type="success",
    error=None
):
    # Ensure data is always a list (wrap it in a list if not)
    if data is None:
        data = []
    elif not isinstance(data, list):
        data = [data]

    response = {
        "status": response_type,
        "message": message,
        "data": data
    }

    if error:
        response["error"] = error

    return Response(response, status=status_code)



def response_switch(case, message="", data=None, error=None):
    from rest_framework import status

    cases = {
        "success": {
            "status": "success",
            "status_code": status.HTTP_200_OK
        },
        "missing": {
            "status": "missing",
            "status_code": status.HTTP_200_OK
        },
        "created": {
            "status": "success",
            "status_code": status.HTTP_201_CREATED
        },
        "bad_request": {
            "status": "failed",
            "status_code": status.HTTP_400_BAD_REQUEST
        },
        "unauthorized": {
            "status": "failed",
            "status_code": status.HTTP_401_UNAUTHORIZED
        },
        "not_found": {
            "status": "failed",
            "status_code": status.HTTP_404_NOT_FOUND
        },
        "server_error": {
            "status": "error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    }

    config = cases.get(case, cases["success"])

    # Add count if data is a list or queryset
    response_data = {
        "message": message,
        "status": config["status"],
    }

    if isinstance(data, (list, tuple)):
        response_data["count"] = len(data)
        response_data["data"] = data
    elif isinstance(data, dict) and "results" in data:
        # For paginated data
        response_data["count"] = data.get("count", len(data["results"]))
        response_data["data"] = data
    else:
        response_data["data"] = data

    if error:
        response_data["error"] = error

    return Response(response_data, status=config["status_code"])

# **************************************************************************************************************************

from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 5  # default page size
    page_size_query_param = 'page_size'  # allow client to set page size using this query param
    max_page_size = 100  # max limit for page size to prevent huge queries


