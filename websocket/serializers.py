# serializers.py

from tortoise.contrib.pydantic import pydantic_model_creator
from .models import *

# -------------------------- Purchase Order --------------------------
PurchaseOrder_Pydantic = pydantic_model_creator(
    purchaseorder_table, name="PurchaseOrder"
)
PurchaseOrderIn_Pydantic = pydantic_model_creator(
    purchaseorder_table, name="PurchaseOrderIn", exclude_readonly=True
)

# -------------------------- Purchase Order Item --------------------------
PurchaseOrderItem_Pydantic = pydantic_model_creator(
    purchaseorder_item_table, name="PurchaseOrderItem"
)
PurchaseOrderItemIn_Pydantic = pydantic_model_creator(
    purchaseorder_item_table, name="PurchaseOrderItemIn", exclude_readonly=True
)

# -------------------------- Packing --------------------------
Packing_Pydantic = pydantic_model_creator(
    packing_table, name="Packing"
)
PackingIn_Pydantic = pydantic_model_creator(
    packing_table, name="PackingIn", exclude_readonly=True
)

# -------------------------- Box Packing --------------------------
BoxPacking_Pydantic = pydantic_model_creator(
    boxpacking_table, name="BoxPacking"
)
BoxPackingIn_Pydantic = pydantic_model_creator(
    boxpacking_table, name="BoxPackingIn", exclude_readonly=True
)
# -------------------------- Box Packing Item--------------------------
BoxPackingItem_Pydantic = pydantic_model_creator(
    boxpacking_item_table, name="BoxPackingItem"
)
BoxPackingItemIn_Pydantic = pydantic_model_creator(
    boxpacking_item_table, name="BoxPackingItemIn", exclude_readonly=True
)

# -------------------------- Delivery --------------------------
Delivery_Pydantic = pydantic_model_creator(
    delivery_table, name="Delivery"
)
DeliveryIn_Pydantic = pydantic_model_creator(
    delivery_table, name="DeliveryIn", exclude_readonly=True
)

# -------------------------- Delivery Item --------------------------
DeliveryItem_Pydantic = pydantic_model_creator(
    delivery_item_table, name="DeliveryItem"
)
DeliveryItemIn_Pydantic = pydantic_model_creator(
    delivery_item_table, name="DeliveryDeliveryItemIn", exclude_readonly=True
)
