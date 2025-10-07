from rest_framework import serializers
from masters.models import *
from websocket.models import *
from .models import *
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import base64
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404
from common.utils import * 
from common.utils import * 
from rest_framework import serializers
from dateutil.parser import parse as parse_date
from masters.serializers import *

from rest_framework.fields import DateTimeField
import datetime


# class PurchaseOrderItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = purchaseorder_item_table
#         fields = ['id', 'size_id', 'quantity', 'description', 'is_active', 'status']
#         extra_kwargs = {field: {'required': False, 'allow_null': True} for field in fields}


# class PurchaseOrderSerializer(serializers.ModelSerializer):
#     items = PurchaseOrderItemSerializer(many=True, write_only=True)  # Nested items

#     class Meta:
#         model = purchaseorder_table
#         fields = [
#             'id', 'company_id', 'fy_id', 'school_id', 'style_id', 'size_id',
#             'po_number', 'order_number', 'order_date', 'barcode',
#             'total_quantity', 'description', 'is_active', 'status',
#             'created_on', 'updated_on', 'created_by', 'updated_by',
#             'items'
#         ]
#         extra_kwargs = {field: {'required': False, 'allow_null': True} for field in fields}

#     def create(self, validated_data):
#         items_data = validated_data.pop('items', [])

#         # Create main order
#         order = purchaseorder_table.objects.create(**validated_data)
        
#         # Create related items
#         for item_data in items_data:
#             purchaseorder_item_table.objects.create(
#                 po_id=order.id,
#                 **item_data
#             )
        
#         return order


class PurchaseOrderItemSerializer(BaseModelSerializer):
    class Meta:
        model = purchaseorder_item_table
        fields = '__all__'


class PurchaseOrderSerializer(BaseModelSerializer):
    # Nested write input
    items_input = PurchaseOrderItemSerializer(many=True, write_only=True, required=False)

    # Computed fields (read-only)
    total_po_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_delivered_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_balance_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    po_status = serializers.CharField(read_only=True)

    po_date = CustomDateTimeField(required=False)

    # Nested read-only output
    items = serializers.SerializerMethodField()

    class Meta:
        model = purchaseorder_table
        fields = [
            'id',
            'company_id',
            'fy_id',
            'school_id',
            'category_id',
            'style_id',
            'size_id',
            'po_number',
            'po_name',
            'order_number',
            'po_date',
            'total_quantity',
            'total_po_quantity',
            'total_delivered_quantity',
            'total_balance_quantity',
            'po_status',
            'description',
            'is_active',
            'status',
            'created_on',
            'updated_on',
            'created_by',
            'updated_by',
            'items_input',  # write-only
            'items',        # read-only
        ]

        read_only_fields = [
            'total_po_quantity',
            'total_delivered_quantity',
            'total_balance_quantity',
            'po_status',
        ]

    def get_items(self, obj):
        # Avoid N+1 queries — assumes prefetch_related is used
        return PurchaseOrderItemSerializer(
            getattr(obj, 'items', purchaseorder_item_table.objects.filter(po_id=obj.id)),
            many=True
        ).data

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items_input', None)
        user = self.context['request'].user

        # Update base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = user.id
        instance.save()

        if items_data is not None:
            # Remove old items
            purchaseorder_item_table.objects.filter(po_id=instance.id).delete()

            # Create new items
            for item in items_data:
                item['po_id'] = instance.id
                item['created_by'] = user.id
                item['updated_by'] = user.id
                purchaseorder_item_table.objects.create(**item)

        return instance
   

# ---------------------------------------------------packing--------------------------------------------------------------------------

class PackingSerializer(BaseModelSerializer):
  
    class Meta:
        model = packing_table
        fields ='__all__'   

# ---------------------------------------------------box packing--------------------------------------------------------------------------

class BoxPackingItemSerializer(BaseModelSerializer):
    class Meta:
        model = boxpacking_item_table
        fields = '__all__'


class BoxPackingSerializer(BaseModelSerializer):
    # Nested write input
    items_input = BoxPackingItemSerializer(many=True, write_only=True, required=False)

    # Nested read-only output
    items = serializers.SerializerMethodField()

    class Meta:
        model = boxpacking_table
        fields = [
            'id',
            'school_id',
            'category_id',
            'style_id',
            'po_id',
            'box_date',
            'box_number',
            'quantity',
            'barcode_str',
            'barcode',
            'description',
            'is_active',
            'status',
            'created_on',
            'updated_on',
            'created_by',
            'updated_by',
            'items_input',  # write-only
            'items',     # read-only
            
        ]

    def get_items(self, obj):
        qs = boxpacking_item_table.objects.filter(box_packing_id=obj.id)
        return BoxPackingItemSerializer(qs, many=True).data

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items_input', None)
        request = self.context.get('request')
        user_id = request.user.id if request else None

        # Ensure po_id exists
        if 'po_id' not in validated_data or not validated_data.get('po_id'):
            validated_data['po_id'] = instance.po_id

        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if user_id:
            instance.updated_by = user_id
        instance.save()

        # Update items if provided
        if items_data is not None:
            boxpacking_item_table.objects.filter(box_packing_id=instance.id).delete()

            for item in items_data:
                item['box_packing_id'] = instance.id
                item['created_by'] = user_id
                item['updated_by'] = user_id
                boxpacking_item_table.objects.create(**item)

        return instance
 

# ---------------------------------------------------delivery--------------------------------------------------------------------------

class DeliveryItemSerializer(BaseModelSerializer):
    class Meta:
        model = delivery_item_table
        fields = '__all__'


class DeliverySerializer(BaseModelSerializer):
    # Nested write input for creating/updating items
    items_input = DeliveryItemSerializer(many=True, write_only=True, required=False)

    # Nested read-only output for items
    items = serializers.SerializerMethodField()
    delivery_date = CustomDateTimeField(required=False)
 
    class Meta:
        model = delivery_table
        fields = [
            'id',
            'school_id',
            'category_id',
            'style_id',
            'po_id',
            'delivery_number',  # fixed field name, not box_number
            'delivery_date',    # fixed field name, not box_date
            'quantity',
            'description',
            'is_active',
            'status',
            'created_on',
            'updated_on',
            'created_by',
            'updated_by',
            'items_input',  # write-only input for nested items
            'items',        # read-only nested items
        ]

    def get_items(self, obj):
        # Fetch delivery items by delivery_id (not box_packing_id)
        qs = delivery_item_table.objects.filter(delivery_id=obj.id)
        return DeliveryItemSerializer(qs, many=True).data

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items_input', None)
        request = self.context.get('request')
        user_id = request.user.id if request else None

        # Ensure po_id exists: fallback to existing if missing
        if not validated_data.get('po_id'):
            validated_data['po_id'] = instance.po_id

        # Update the delivery fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if user_id:
            instance.updated_by = user_id
        instance.save()

        # Update nested delivery items if provided
        if items_data is not None:
            # Delete existing items for this delivery
            delivery_item_table.objects.filter(delivery_id=instance.id).delete()

            # Create new items, setting audit fields
            for item in items_data:
                item['delivery_id'] = instance.id
                item['created_by'] = user_id
                item['updated_by'] = user_id
                delivery_item_table.objects.create(**item)

        return instance

