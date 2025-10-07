from django.db import models
from datetime import datetime
from django.core.exceptions import ValidationError
from masters.models import *
from masters.utils import *
from django.utils import timezone
import os
from django.db.models import Max



# Create your models here.

def save_file_sync(file: bytes, filename: str) -> str:
    folder_path = "media/barcodes"
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, filename)

    if hasattr(file, "read"):
        file.seek(0)
        file = file.read()

    with open(filepath, 'wb') as out_file:
        out_file.write(file)

    return filepath


# def generate_sequential_number(model_class, field_name='order_number', prefix='', padding=4):
#     last_obj = model_class.objects.filter(**{f"{field_name}__startswith": prefix}).order_by(f"-{field_name}").first()
#     if last_obj:
#         val = getattr(last_obj, field_name)
#         try:
#             last_num = int(val[len(prefix):])
#         except (ValueError, TypeError):
#             last_num = 0
#     else:
#         last_num = 0

#     next_num = last_num + 1
#     return f"{prefix}{str(next_num).zfill(padding)}"

def generate_sequential_number(model_class, field_name='order_number', prefix=''):
    last_obj = model_class.objects.filter(**{f"{field_name}__startswith": prefix}).order_by(f"-{field_name}").first()
    if last_obj:
        val = getattr(last_obj, field_name)
        try:
            last_num = int(val[len(prefix):])
        except (ValueError, TypeError):
            last_num = 0
    else:
        last_num = 0

    next_num = last_num + 1
    return f"{prefix}{next_num}"


 
class purchaseorder_table(models.Model):
    company_id = models.IntegerField(null=True)
    fy_id = models.IntegerField(null=True)
    school_id = models.IntegerField(null=True)
    category_id = models.IntegerField(null=True)
    style_id = models.IntegerField(null=True)
    size_id = models.IntegerField(null=True) 
    po_number = models.CharField(max_length=20, unique=True, null=True)
    po_name = models.CharField(max_length=20, unique=True, null=True)
    order_number = models.CharField(max_length=20, unique=True, null=True)
    po_date = models.DateTimeField(default=datetime.now)
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = models.CharField(max_length=150, null=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "tm_order"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_sequential_number(purchaseorder_table, field_name='order_number', prefix='ORD')

        if not self.po_number:
            self.po_number = generate_sequential_number(purchaseorder_table, field_name='po_number', prefix='PO')

        super().save(*args, **kwargs)
 

class purchaseorder_item_table(models.Model):
    po_id = models.IntegerField(null=True)
    size_id = models.IntegerField(null=True)
    color_id = models.IntegerField(null=True)
    quantity = models.IntegerField(null=True)
    barcode = models.CharField(max_length=255, null=True)  # path to saved barcode image
    barcode_str = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=150, null=True)
    serial_number = models.IntegerField(null=True, blank=True)

    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "tx_order"  

    def save(self, *args, **kwargs):
        # --- Fetch and validate PO ---
        po = purchaseorder_table.objects.filter(id=self.po_id, status=1).first()
        if not po:
            raise ValidationError("Invalid Purchase Order ID")

        year = po.po_date.year if po.po_date else timezone.now().year
        year_short = str(year)[-2:]
        po_number = po.po_number
        if not po_number:
            raise ValidationError("PO number is missing")
            
        # Get school short name — no fallback!
        school_short = get_fields_by_id(school_table, po.school_id, "short_name")
        if not school_short:
            raise ValidationError(["Missing school short name for barcode"]) 
        
        # Get style short code or name — strict validation
        style_obj = tm_style_table.objects.filter(id=po.style_id).first()  
        if not style_obj:
            raise ValidationError(["Style not found for given style_id"]) 
                
        style_short = getattr(style_obj, 'short_code', None) or getattr(style_obj, 'name', None)
        if not style_short:
            raise ValidationError(["Missing style short code or name for barcode"])

        # --- Fetch and validate color code --- 
        color_code = get_fields_by_id(color_table, self.color_id, "short_name") \
             or get_fields_by_id(color_table, self.color_id, "name")
        if not color_code:
            raise ValidationError("Color short code or name is missing")

        # --- Fetch and validate size code --- 
        size_code = get_fields_by_id(size_table, self.size_id, "name")   
            
        if not size_code:
            raise ValidationError("Size short code or name is missing")

        # --- Generate serial number if missing ---
        if self.serial_number is None:
            # Check if this combo (PO + color + size) already exists
            existing_item = purchaseorder_item_table.objects.filter(
                po_id=self.po_id,
                color_id=self.color_id,
                size_id=self.size_id,
                is_active=1,
                status=1
            ).exclude(pk=self.pk).first()

            if existing_item and existing_item.serial_number:
                self.serial_number = existing_item.serial_number  # Use existing serial
            else:
                # If not found, assign next available serial globally for this color-size combo
                last_serial = purchaseorder_item_table.objects.filter(
                    color_id=self.color_id,
                    size_id=self.size_id,
                    is_active=1,
                    status=1
                ).exclude(pk=self.pk).aggregate(Max('serial_number'))['serial_number__max'] or 0

                self.serial_number = last_serial + 1
 

        serial_str = f"{self.serial_number:02d}"
        barcode_data = f"{year_short}/{po_number}-{school_short}-{style_short}-{color_code}-{size_code}"    
        self.barcode_str = barcode_data

        filename = barcode_data.replace("/", "_")

        # --- Fetch and validate category and style ---
        category_name = get_fields_by_id(category_table, po.category_id, "name")
        if not category_name:
            raise ValidationError("Category name is missing")

        style_name = get_fields_by_id(tm_style_table, po.style_id, "name")
        if not style_name:
            raise ValidationError("Style name is missing")

        # --- Generate barcode image ---
        barcode_file, filename = generate_custom_barcode_image(
            brand="Vihaan",
            details_line=f"{category_name} / {style_name} / {color_code}-{size_code}", 
            barcode_string=barcode_data,
            filename=filename 
        )
        barcode_path = save_file_sync(barcode_file, filename)
        self.barcode = barcode_path

        super().save(*args, **kwargs)   
 

class packing_table(models.Model): 
    school_id = models.IntegerField(null=True)
    po_id = models.IntegerField(null=True)
    size_id = models.IntegerField(null=True)
    color_id =  models.IntegerField(null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = models.CharField(max_length=150, null=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "order_entry" 

class boxpacking_table(models.Model):
    school_id = models.IntegerField(null=True)
    category_id = models.IntegerField(null=True)
    style_id = models.IntegerField(null=True)
    po_id = models.IntegerField(null=True)  # Must be set before saving

    box_date = models.DateTimeField(default=datetime.now)
    box_number = models.CharField(max_length=20, unique=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    barcode_str = models.CharField(max_length=255, null=True, blank=True)  # barcode string
    barcode = models.CharField(max_length=255, null=True, blank=True)      # barcode image path

    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "tm_box_packing"

    def save(self, *args, **kwargs):
        # Ensure po_id is present
        if not self.po_id:
            raise ValidationError(["po_id must be set before saving BoxPacking"])

        # Generate unique box number if not set
        if not self.box_number:
            self.box_number = generate_sequential_number(
                boxpacking_table,
                field_name='box_number',
                prefix='BX'
            )

        # If barcode is not yet generated
        if self.box_number and not self.barcode:
            po = purchaseorder_table.objects.filter(id=self.po_id, status=1).first()
            if not po:
                raise ValidationError(["Invalid Purchase Order for given po_id"])

            year = po.po_date.year if po.po_date else timezone.now().year
            year_short = str(year)[-2:]

            # Get school short name — no fallback!
            school_short = get_fields_by_id(school_table, po.school_id, "short_name")
            if not school_short:
                raise ValidationError(["Missing school short name for barcode"])

            # Get style short code or name — strict validation
            style_obj = tm_style_table.objects.filter(id=self.style_id).first()
            if not style_obj:
                raise ValidationError(["Style not found for given style_id"])

            style_short = getattr(style_obj, 'short_code', None) or getattr(style_obj, 'name', None)
            if not style_short:
                raise ValidationError(["Missing style short code or name for barcode"])

            # Get PO number
            po_number = po.po_number
            if not po_number:
                raise ValidationError(["Missing PO number for barcode"])

            # Build barcode string
            barcode_string = f"{year_short}/{po_number}-{school_short}-{style_short}-{self.box_number}"
            self.barcode_str = barcode_string

            filename = barcode_string.replace("/", "_")

            # Generate barcode image
            barcode_file, filename = generate_custom_barcode_image(
                brand="Vihaan",
                details_line=f"{year_short} / {po_number} / {school_short} / {style_short}",
                barcode_string=barcode_string,
                filename=filename
            )

            self.barcode = save_file_sync(barcode_file, filename)

        super().save(*args, **kwargs)


class boxpacking_item_table(models.Model):
    box_packing_id = models.IntegerField(null=False)
    po_id = models.IntegerField(null=True)  # auto-filled from barcode_str
    barcode = models.CharField(max_length=255, null=False)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "tx_box_packing"

    # def save(self, *args, **kwargs):
    #     if not self.po_id:
    #         clean_barcode = self.barcode.strip()
    #         matched_item = purchaseorder_item_table.objects.filter(
    #             barcode_str__iexact=clean_barcode,
    #             status=1
    #         ).first()
    #         if matched_item:
    #             self.po_id = matched_item.po_id
    #         else:
    #             raise ValidationError([f"No matching purchase order item found for barcode: {self.barcode}"])

    #     super().save(*args, **kwargs)


class delivery_table(models.Model):
    school_id = models.IntegerField(null=True)
    category_id = models.IntegerField(null=True)
    style_id = models.IntegerField(null=True)
    po_id = models.IntegerField(null=True) 
    delivery_number = models.CharField(max_length=20, unique=True, null=True)
    delivery_date = models.DateTimeField(default=timezone.now)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "delivery"

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = generate_sequential_number(delivery_table, field_name='delivery_number', prefix='DEL')
        super().save(*args, **kwargs)


class delivery_item_table(models.Model):
    delivery_id = models.IntegerField(null=False)  # references delivery_table.id
    box_packing_id = models.IntegerField(null=False)  # references boxpacking_table.id
    barcode = models.CharField(max_length=255, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "delivery_item"
