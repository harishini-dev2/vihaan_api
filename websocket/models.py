
from tortoise.exceptions import ValidationError
from tortoise.functions import Max
from datetime import datetime
import os
import pytz
from asgiref.sync import sync_to_async

from masters.utils import generate_custom_barcode_image, get_fields_by_id
from masters.models import *

from tortoise import fields, models






# Timezone object for Asia/Kolkata
india_tz = pytz.timezone('Asia/Kolkata')

async def save_file_async(file: bytes, filename: str) -> str:
    folder_path = "media/barcodes"
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, filename)

    if hasattr(file, "read"):
        file.seek(0)
        file = file.read()

    import aiofiles
    async with aiofiles.open(filepath, 'wb') as out_file:
        await out_file.write(file)

    return filepath

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
    company_id = fields.IntField(null=True)
    fy_id = fields.IntField(null=True)
    school_id = fields.IntField(null=True)
    category_id = fields.IntField(null=True)
    style_id = fields.IntField(null=True)
    size_id = fields.IntField(null=True)
    po_number = fields.CharField(max_length=20, unique=True, null=True)
    po_name = fields.CharField(max_length=20, unique=True, null=True)
    order_number = fields.CharField(max_length=20, unique=True, null=True)
    po_date = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    total_quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "purchaseorder_table"

    async def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = await generate_sequential_number(
                purchaseorder_table, field_name='order_number', prefix='ORD', padding=4)
        if not self.po_number:
            self.po_number = await generate_sequential_number(
                purchaseorder_table, field_name='po_number', prefix='PO', padding=4)
        await super().save(*args, **kwargs)


class purchaseorder_item_table(models.Model):
    po_id = fields.IntField(null=True)
    size_id = fields.IntField(null=True)
    color_id = fields.IntField(null=True)
    quantity = fields.IntField(null=True)
    barcode = fields.CharField(max_length=255, null=True)
    barcode_str = fields.CharField(max_length=255, null=True)
    description = fields.CharField(max_length=150, null=True)
    serial_number = fields.IntField(null=True)

    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "purchaseorder_item_table"

    async def save(self, *args, **kwargs):
        po = await purchaseorder_table.filter(id=self.po_id, status=1).first()
        if not po:
            raise ValidationError("Invalid Purchase Order ID")

        year = po.po_date.year if po.po_date else datetime.now(india_tz).year
        year_short = str(year)[-2:]
        po_number = po.po_number
        if not po_number:
            raise ValidationError("PO number is missing")

        # Use sync_to_async for get_fields_by_id calls if sync
        color_code = await sync_to_async(get_fields_by_id)('color_table', self.color_id, "short_name") \
            or await sync_to_async(get_fields_by_id)('color_table', self.color_id, "name")
        if not color_code:
            raise ValidationError("Color short code or name is missing")

        size_code = await sync_to_async(get_fields_by_id)('size_table', self.size_id, "name") \
            or await sync_to_async(get_fields_by_id)('size_table', self.size_id, "name")
        if not size_code:
            raise ValidationError("Size short code or name is missing")

        if self.serial_number is None:
            existing_item = await purchaseorder_item_table.filter(
                po_id=self.po_id,
                color_id=self.color_id,
                size_id=self.size_id,
                is_active=1,
                status=1
            ).exclude(id=self.id).first()

            if existing_item and existing_item.serial_number:
                self.serial_number = existing_item.serial_number
            else:
                last_serial_record = await purchaseorder_item_table.filter(
                    color_id=self.color_id,
                    size_id=self.size_id,
                    is_active=1,
                    status=1
                ).exclude(id=self.id).annotate(max_serial=Max('serial_number')).first()

                last_serial = last_serial_record.max_serial if last_serial_record and last_serial_record.max_serial else 0
                self.serial_number = last_serial + 1

        serial_str = f"{self.serial_number:02d}"
        barcode_data = f"{year_short}-{po_number}-{color_code}-{size_code}-{serial_str}"
        self.barcode_str = barcode_data

        category_name = await sync_to_async(get_fields_by_id)('category_table', po.category_id, "name")
        if not category_name:
            raise ValidationError("Category name is missing")

        style_name = await sync_to_async(get_fields_by_id)('tm_style_table', po.style_id, "name")
        if not style_name:
            raise ValidationError("Style name is missing")

        # Wrap barcode generation in sync_to_async if it is sync
        barcode_file, filename = await sync_to_async(generate_custom_barcode_image)(
            brand="Vihaan",
            details_line=f"{category_name} / {style_name} / {color_code}-{size_code}",
            barcode_string=barcode_data,
            filename=barcode_data
        )

        # Use async file save
        barcode_path = await save_file_async(barcode_file, filename)
        self.barcode = barcode_path

        await super().save(*args, **kwargs)


class packing_table(models.Model):
    school_id = fields.IntField(null=True)
    po_id = fields.IntField(null=True)
    size_id = fields.IntField(null=True)
    color_id = fields.IntField(null=True)
    quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "packing_table"


class boxpacking_table(models.Model):
    school_id = fields.IntField(null=True)
    category_id = fields.IntField(null=True)
    style_id = fields.IntField(null=True)
    po_id = fields.IntField(null=True)

    box_date = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    box_number = fields.CharField(max_length=20, unique=True, null=True)
    quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)

    barcode_str = fields.CharField(max_length=255, null=True)
    barcode = fields.CharField(max_length=255, null=True)

    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "boxpacking_table"

    async def save(self, *args, **kwargs):
        if not self.po_id:
            raise ValidationError("po_id must be set before saving BoxPacking")

        if not self.box_number:
            self.box_number = await generate_sequential_number(
                boxpacking_table, field_name='box_number', prefix='BX', padding=4)

        if self.box_number and not self.barcode:
            po = await purchaseorder_table.filter(id=self.po_id, status=1).first()
            if not po:
                raise ValidationError("Invalid Purchase Order for given po_id")

            year = po.po_date.year if po.po_date else datetime.now(india_tz).year
            year_short = str(year)[-2:]

            school_short = await sync_to_async(get_fields_by_id)('school_table', po.school_id, "short_name")
            if not school_short:
                raise ValidationError("Missing school short name for barcode")

            style_obj = await tm_style_table.filter(id=self.style_id).first()
            if not style_obj:
                raise ValidationError("Style not found for given style_id")

            style_short = getattr(style_obj, 'short_code', None) or getattr(style_obj, 'name', None)
            if not style_short:
                raise ValidationError("Missing style short code or name for barcode")

            po_number = po.po_number
            if not po_number:
                raise ValidationError("Missing PO number for barcode")

            barcode_string = f"{year_short}/{po_number}/{school_short}/{style_short}/{self.box_number}"
            self.barcode_str = barcode_string

            filename = barcode_string.replace("/", "_")

            barcode_file, filename = await sync_to_async(generate_custom_barcode_image)(
                brand="Vihaan",
                details_line=f"{year_short} / {po_number} / {school_short} / {style_short}",
                barcode_string=barcode_string,
                filename=filename
            )

            self.barcode = await save_file_async(barcode_file, filename)

        await super().save(*args, **kwargs)


class boxpacking_item_table(models.Model):
    box_packing_id = fields.IntField()
    po_id = fields.IntField(null=True)
    barcode = fields.CharField(max_length=255)
    quantity = fields.DecimalField(max_digits=10, decimal_places=2)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "boxpacking_item_table"

    async def save(self, *args, **kwargs):
        if not self.po_id:
            clean_barcode = self.barcode.strip()
            matched_item = await purchaseorder_item_table.filter(
                barcode_str__iexact=clean_barcode,
                status=1
            ).first()
            if matched_item:
                self.po_id = matched_item.po_id
            else:
                raise ValidationError(f"No matching purchase order item found for barcode: {self.barcode}")

        await super().save(*args, **kwargs)


class delivery_table(models.Model):
    school_id = fields.IntField(null=True)
    po_id = fields.IntField(null=True)
    delivery_date = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    quantity = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "delivery_table"


class delivery_item_table(models.Model):
    delivery_id = fields.IntField()
    po_id = fields.IntField(null=True)
    barcode = fields.CharField(max_length=255)
    quantity = fields.DecimalField(max_digits=10, decimal_places=2)
    description = fields.CharField(max_length=150, null=True)
    is_active = fields.IntField(default=1)
    status = fields.IntField(default=1)
    created_on = fields.DatetimeField(default=lambda: datetime.now(india_tz))
    updated_on = fields.DatetimeField(auto_now=True)
    created_by = fields.IntField(null=True)
    updated_by = fields.IntField(null=True)

    class Meta:
        table = "delivery_item_table"

    async def save(self, *args, **kwargs):
        if not self.po_id:
            clean_barcode = self.barcode.strip()
            matched_item = await purchaseorder_item_table.filter(
                barcode_str__iexact=clean_barcode,
                status=1
            ).first()
            if matched_item:
                self.po_id = matched_item.po_id
            else:
                raise ValidationError(f"No matching purchase order item found for barcode: {self.barcode}")

        await super().save(*args, **kwargs)
