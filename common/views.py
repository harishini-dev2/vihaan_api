from django.shortcuts import render

# Create your views here.

import json
from django.conf import settings
from django.shortcuts import render
from common.utils import *

import hashlib
import os
from django.utils import timezone
from django.db.models import Max, F, Q
import base64
from io import BytesIO
from django.template.loader import get_template
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static

from django.contrib.staticfiles import finders
from common.utils import *
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework.response import Response

from rest_framework.decorators import api_view
from rest_framework import generics
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password, check_password
from .models import *
from masters.models import * 
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters import rest_framework as filters
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from hashlib import md5
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
import calendar
from django.db.models import Count, Q
import uuid
from django.utils.crypto import get_random_string
import random
import requests
from requests.exceptions import RequestException
from django.core.mail import EmailMessage, get_connection,send_mail
from rest_framework.exceptions import AuthenticationFailed
import requests
from django.db import connection
from django.core.exceptions import MultipleObjectsReturned
from rest_framework_simplejwt.exceptions import TokenError

#``````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````

class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            device_id = request.data.get('device_id')
            fcm_token = request.data.get('fcm_token')
            date_times = timezone.localtime(timezone.now())
            if not username or not password:
                return response_switch(
                    "bad_request",
                    message="Username and password are required",
                    data=[]
                )

            # password_hash = hashlib.md5(str(password).encode()).hexdigest()

            employee_qs = employee_table.objects.filter(
                username=username, password=password, status=1
            )
            if not employee_qs.exists():
                return response_switch(
                    "bad_request",
                    message="Employee not exists",
                    data=[]
                )

            employee = employee_qs.first()

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'username': username}
            )
            if created:
                user.set_password('temporary_password')
                user.save()

            employee.auth_id = user.id
            employee.device_id = device_id
            employee.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            session_table.objects.create(
                device_id=device_id,
                employee_id=employee.id,
                auth_id=user.id,
                fcm_token=fcm_token,
                latitude=None,
                longitude=None,
                timestamp=str(timezone.localtime(timezone.now())),
                session_token=access_token,
                is_active=1,
                status=1,
                created_on=date_times,
                updated_on=date_times
            )

            try:
                token = AccessToken(access_token)
                user_id_from_token = token['user_id']
            except Exception as e:
                return response_switch(
                    "unauthorized",
                    message="Invalid token",
                    error=str(e)
                )

            request.session['auth_id'] = user_id_from_token
            request.session['employee_id'] = employee.id
           

            # Get user privileges
            # role_id = getattr(employee, 'user_role_id', None)
            # privilege_data = []

            # if role_id:
            #     privileges = user_privilege_table.objects.filter(role_id=role_id, status=1)
            #     for priv in privileges:
            #         module = user_modules_table.objects.filter(id=priv.module_id).first()
            #         if module:
            #             privilege_data.append({
            #                 "module": module.name,
            #                 "create": priv.is_create,
            #                 "read": priv.is_read,
            #                 "update": priv.is_update,
            #                 "delete": priv.is_delete,
            #             })
           
            
            return response_switch(
                "success",
                message="Logged in successfully.",
                data={
                    'refresh': str(refresh),
                    'access': access_token,
                    'auth_id': user.id,
                    'user_id': employee.id,
                    'device_id': device_id,
                    'fcm_token': fcm_token,
                    
                    'company_name': '-',
                    'id': employee.id,
                    'name': employee.username,
                    
                    'email': employee.email,
                    'created_by': employee.id,            
                    'updated_by': employee.id, 
                                                
                }
            )

        except Exception as e:
            return response_switch(
                "bad_request",
                message="An unexpected error occurred during login.",
                error=str(e)
            )



#``````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````

class TokenRefreshView(APIView):
        def post(self, request):
            try:
                refresh_token = request.data.get('refresh')
                token = RefreshToken(refresh_token)
                new_access_token = str(token.access_token)
                return Response({"access": new_access_token}, status=status.HTTP_200_OK)
            except TokenError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)