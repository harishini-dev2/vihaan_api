from django.contrib.auth import views as auth_views
from common.views import * 
from django.urls import path, include


urlpatterns = [
    # login
    path('auth/login/', LoginView.as_view(), name='login'), 

    # refresh token
    path('auth/refresh-token/', TokenRefreshView.as_view(), name='refresh-token'),

]

