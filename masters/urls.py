from django.urls import path
from  masters import views
from .company import *
from .financial_year import *
from .employee import *
from .category import *
from .color import *
from .school import *
from .style import *
from .size import *

urlpatterns=[

    # home
    path('',views.home),

    # company
    path('company-details/', CompanyDetailAPIView.as_view(), name='company-details'),
    path('company-update/', CompanyUpdate.as_view(), name='company-update'), 

    # financial-year
    path('financial-year-add/', FinancialYearAddAPIView.as_view(), name='financial-year-add'),
    path('financial-year-list/', FinancialYearListAPIView.as_view(), name='financial-year-list'),
    path('financial-year-update/', FinancialYearUpdate.as_view(), name='financial-year-update'), 
    path('financial-year-delete/', FinancialYearDeleteAPIView.as_view(), name='financial-year-delete'),

    # employee
    path('employee-add/', EmployeeAddAPIView.as_view(), name='employee-add'),
    path('employee-list/', EmployeeListAPIView.as_view(), name='employee-list'),
    path('employee-details/', EmployeeDetailAPIView.as_view(), name='employee-details'),
    path('employee-update/', EmployeeUpdate.as_view(), name='employee-update'), 
    path('employee-delete/', EmployeeDeleteAPIView.as_view(), name='employee-delete'),


    # category
    path('category-add/', CategoryAddAPIView.as_view(), name='category-add'),
    path('category-list/', CategoryListAPIView.as_view(), name='category-list'),
    path('category-details/', CategoryDetailAPIView.as_view(), name='category-details'),
    path('category-update/', CategoryUpdate.as_view(), name='category-update'), 
    path('category-delete/', CategoryDeleteAPIView.as_view(), name='category-delete'),
    
    # color
    path('color-add/', ColorAddAPIView.as_view(), name='color-add'),
    path('color-list/', ColorListAPIView.as_view(), name='color-list'),
    path('color-details/', ColorDetailAPIView.as_view(), name='color-details'),
    path('color-update/', ColorUpdate.as_view(), name='color-update'), 
    path('color-delete/', ColorDeleteAPIView.as_view(), name='color-delete'),


    # school
    path('school-add/', SchoolAddAPIView.as_view(), name='school-add'),
    path('school-list/', SchoolListAPIView.as_view(), name='school-list'),
    path('school-details/', SchoolDetailAPIView.as_view(), name='school-details'), 
    path('school-update/', SchoolUpdate.as_view(), name='school-update'), 
    path('school-delete/', SchoolDeleteAPIView.as_view(), name='school-delete'),

    # size
    path('size-add/', SizeAddAPIView.as_view(), name='size-add'),
    path('size-list/', SizeListAPIView.as_view(), name='size-list'),
    path('size-details/', SizeDetailAPIView.as_view(), name='size-details'),
    path('size-update/', SizeUpdate.as_view(), name='size-update'),  
    path('size-delete/', SizeDeleteAPIView.as_view(), name='size-delete'),
    
    # common style 
    path('style-add/', StyleAddAPIView.as_view(), name='style-add'),
    path('style-list/', StyleListAPIView.as_view(), name='style-list'),
    path('style-update/', StyleUpdate.as_view(), name='style-update'),
    # tm_style
    path('tm-style-details/', StyleTmDetailAPIView.as_view(), name='tm-style-details'),  
    path('tm-style-delete/', StyleTmDeleteAPIView.as_view(), name='tm-style-delete'),
    # tx_style
    path('tx-style-details/', StyleTxDetailAPIView.as_view(), name='tx-style-details'),
    path('tx-style-delete/', StyleTxDeleteAPIView.as_view(), name='tx-style-delete'),

    

]