from rest_framework import serializers
from .models import  *

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import base64
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404
from .utils import * 

from rest_framework import serializers
from dateutil.parser import parse as parse_date

from rest_framework.fields import DateTimeField
import datetime

# ---------------------------------------------------common codes--------------------------------------------------------------------------
# date time 
class CustomDateTimeField(DateTimeField):
    def to_representation(self, value):
        if value is None:
            return None
        # Ensure timezone-aware datetime is converted to local time before formatting
        value = timezone.localtime(value)
        return value.strftime('%d-%m-%Y %H:%M:%S')

    def to_internal_value(self, value):
        if not value:
            return None
        if isinstance(value, datetime.datetime):
            return value
        try:
            return parse_date(value)
        except (ValueError, TypeError):
            self.fail('invalid', format='DD-MM-YYYY HH:MM:SS', input=value)

# common serilaizer function 
class BaseModelSerializer(serializers.ModelSerializer):
    created_on = CustomDateTimeField(required=False)
    updated_on = CustomDateTimeField(required=False)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Automatically apply extra_kwargs for all fields
        cls.Meta.extra_kwargs = {field: {"required": False, "allow_null": True} for field in cls.Meta.fields}

# ---------------------------------------------------company--------------------------------------------------------------------------

class CompanySerializer(BaseModelSerializer):
      
    class Meta:
        model = company_table
        fields ='__all__'
        

# ---------------------------------------------------financial year--------------------------------------------------------------------------

class FinancialYearSerializer(BaseModelSerializer):
  
    class Meta:
        model = financialyear_table
        fields ='__all__'
        

# ---------------------------------------------------employee--------------------------------------------------------------------------

class EmployeeSerializer(BaseModelSerializer):
      
    class Meta:
        model = employee_table
        fields ='__all__'
        

# ---------------------------------------------------category--------------------------------------------------------------------------

class CategorySerializer(BaseModelSerializer):
       
    class Meta:
        model = category_table
        fields ='__all__'
        
# ---------------------------------------------------color--------------------------------------------------------------------------

class ColorSerializer(BaseModelSerializer):
   
    class Meta:
        model = color_table
        fields ='__all__'
        
# ---------------------------------------------------school--------------------------------------------------------------------------

class SchoolSerializer(BaseModelSerializer):
 
    class Meta:
        model = school_table
        fields ='__all__'
        
# ---------------------------------------------------size--------------------------------------------------------------------------

class SizeSerializer(BaseModelSerializer):
       
    class Meta:
        model = size_table
        fields ='__all__'
        
# ---------------------------------------------------style--------------------------------------------------------------------------

class StyleTxSerializer(BaseModelSerializer):
       
    class Meta:
        model = tx_style_table
        fields ='__all__'


class StyleTmSerializer(BaseModelSerializer):
    size_items = serializers.SerializerMethodField()  # read-only nested data
    size_items_input = StyleTxSerializer(many=True, write_only=True, required=False)  # write-only input
    
    class Meta:
        model = tm_style_table
        fields = [
            'id',
            'school_id',
            'category_id',
            'color_ids',
            'name',
            'style_code',
            'description',
            'is_active',
            'status',
            'created_on',
            'updated_on',
            'created_by',
            'updated_by',
            'size_items',  # Put this at the end # for output
            'size_items_input', # for input only
        ]

    def get_size_items(self, obj):
        size_items_qs = tx_style_table.objects.filter(style_id=obj.id)
        return StyleTxSerializer(size_items_qs, many=True).data

    def update(self, instance, validated_data):
        # Pop write-only input field
        size_items_data = validated_data.pop('size_items_input', None)
        validated_data.pop('created_on', None)

        # Update main fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if size_items_data is not None:
            tx_style_table.objects.filter(style_id=instance.id).delete()
            for item in size_items_data:
                tx_style_table.objects.create(style_id=instance.id, **item)

        return instance




# class StyleTmSerializer(BaseModelSerializer):
#     size_items = StyleTxSerializer(many=True, required=False)
    
#     class Meta:
#         model = tm_style_table
#         fields = [
#             'id',
#             'school_id',
#             'category_id',
#             'color_ids',
#             'name',
#             'style_code',
#             'description',
#             'is_active',
#             'status',
#             'created_on',
#             'updated_on',
#             'created_by',
#             'updated_by',
#             'size_items',
#         ]

#     def update(self, instance, validated_data):
#         size_items_data = validated_data.pop('size_items', None)

#         # Prevent 'created_on' from being updated (preserve original)
#         validated_data.pop('created_on', None)

#         # Update fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Replace size_items if provided
#         if size_items_data is not None:
#             tx_style_table.objects.filter(style_id=instance.id).delete()
#             for item in size_items_data:
#                 tx_style_table.objects.create(style_id=instance.id, **item)

#         return instance
