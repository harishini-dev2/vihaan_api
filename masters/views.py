
from django.shortcuts import render
from common.utils import *
from .models import *
from .serializers import *
from common.views import * 
from django.db import transaction

# Create your views here.

def home(request):
    return render (request, "index.html")

