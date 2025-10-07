from tortoise import fields, models
from tortoise.exceptions import ValidationError
from datetime import datetime
from masters.utils import generate_sequential_number, get_fields_by_id, generate_barcode_image
from masters.models import school_table, tm_style_table, size_table
import pytz
from asgiref.sync import sync_to_async  # <-- Added this import


# Get Asia/Kolkata timezone object
india_tz = pytz.timezone('Asia/Kolkata')

async def generate_sequential_number(model_class, field_name='order_number', prefix='', padding=4):
    last_obj = await model_class.filter(**{f"{field_name}__startswith": prefix}).order_by(f"-{field_name}").first()
    if last_obj:
        val = getattr(last_obj, field_name)
        try:
            last_num = int(val[len(prefix):])
        except (ValueError, TypeError):
            last_num = 0
    else:
        last_num = 0

    next_num = last_num + 1
    return f"{prefix}{str(next_num).zfill(padding)}"



class purchaseorder_table(models.Model):
    id = fields.IntField(pk=True)
    company_id = fields.IntField(null=True)
    fy_id = fields.IntField(null=True)
    school_id = fields.IntField(null=True)
    category_id=fields.IntField(null=True)
    style_id = fields.IntField(null=True)
    size_id = fields.IntField(null=True)
    po_number = fields.CharField(max_length=20, unique=True, null=True)
    po_name = fields.CharField(max_length=20, unique=True, null=True)
    order_number = fields.CharField(max_length=20, unique=True, null=True)
    po_date = fields.DatetimeField(default=datetime.now) 
    barcode = fields.CharField(max_length=255, null=True)  # storing filepath for barcode image
    total_quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz), null=True)
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "ws_tm_order"

    async def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = await generate_sequential_number(
                purchaseorder_table, field_name='order_number', prefix='ORD', padding=4
            )
        if not self.po_number:
            self.po_number = await generate_sequential_number(
                purchaseorder_table, field_name='po_number', prefix='PO', padding=4
            )
   

        if self.po_number and not self.barcode:
            # Wrap synchronous calls in sync_to_async
            school_short = await sync_to_async(get_fields_by_id)(school_table, self.school_id, "short_name")
            style_name = await sync_to_async(get_fields_by_id)(tm_style_table, self.style_id, "name")
            size_name = await sync_to_async(get_fields_by_id)(size_table, self.size_id, "name")

            if all("-" not in val for val in [school_short, style_name, size_name]):
                barcode_data = f"{school_short}_{style_name}_{size_name}_{self.po_number}"
                barcode_file, filename = await sync_to_async(generate_barcode_image)(barcode_data, barcode_data)
                barcode_path = await save_file_async(barcode_file, filename)
                self.barcode = barcode_path
            else:
                raise ValidationError("Missing related field(s): school, style, or size")

         # your barcode logic here
        await super().save(*args, **kwargs)



class purchaseorder_item_table(models.Model):
    id = fields.IntField(pk=True)
    po_id = fields.IntField(null=True)
    size_id = fields.IntField(null=True)
    quantity = fields.IntField(null=True) 
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz), null=True)
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "ws_tx_order"


class packing_table(models.Model):
    id = fields.IntField(pk=True)
    school_id = fields.IntField(null=True)
    po_id = fields.IntField(null=True)
    quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz), null=True)
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "ws_packing"


class box_packing_table(models.Model):
    id = fields.IntField(pk=True)
    school_id = fields.IntField(null=True)
    po_id = fields.IntField(null=True)
    style_id = fields.IntField(null=True)
    box_number = fields.CharField(max_length=20, unique=True,null=True)
    quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    barcode = fields.CharField(max_length=255, null=True)  # store filepath for barcode image
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz), null=True)
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "ws_box_packing"

    async def save(self, *args, **kwargs):
        
        if not self.box_number:
            self.box_number = await generate_sequential_number(
                box_packing_table, field_name='box_number', prefix='BX', padding=4)

        if self.box_number and not self.barcode:
            school_short = await sync_to_async(get_fields_by_id)(school_table, self.school_id, "short_name")
            style_name = await sync_to_async(get_fields_by_id)(tm_style_table, self.style_id, "name")
            po_number = await sync_to_async(get_fields_by_id)(purchaseorder_table, self.po_id, "po_number")

            if all("-" not in val for val in [school_short, style_name, po_number]):
                barcode_data = f"{school_short}_{style_name}_{self.box_number}_{po_number}"
                barcode_file, filename = await generate_barcode_image(barcode_data, barcode_data)
                barcode_path = await save_file_async(barcode_file, filename)
                self.barcode = barcode_path
            else:
                raise ValidationError("Missing related field(s): school, style, or size")

        await super().save(*args, **kwargs)


class delivery_table(models.Model):
    id = fields.IntField(pk=True)
    po_id = fields.IntField(null=True)
    order_number = fields.CharField(max_length=20, unique=True, null=True)
    order_date = fields.DatetimeField(default=datetime.now)
    quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz), null=True)
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "ws_delivery" 

    async def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = await generate_sequential_number(
                delivery_table, field_name='order_number', prefix='DEL', padding=4)

        await super().save(*args, **kwargs)


# Helper async function you need to implement:
import os
import aiofiles


async def save_file_async(file: bytes, filename: str) -> str:
    """
    Saves a bytes file asynchronously to disk and returns the filepath.
    
    :param file: File content as bytes or BytesIO
    :param filename: Desired file name
    :return: Path to saved file
    """
    folder_path = "media/barcodes"
    os.makedirs(folder_path, exist_ok=True)  # Ensure the directory exists

    filepath = os.path.join(folder_path, filename)

    # If file is BytesIO, get raw bytes
    if hasattr(file, "read"):
        file.seek(0)
        file = file.read()

    async with aiofiles.open(filepath, 'wb') as out_file:
        await out_file.write(file)

    return filepath


