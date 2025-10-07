
    # yourapp/utils.py

from django.core.exceptions import ObjectDoesNotExist

def get_fields_by_id(model_class, obj_id, field_names):
    """
    Get field values from a model object by ID.

    :param model_class: Django model class
    :param obj_id: Object ID
    :param field_names: String or list/tuple of field names
    :return: Dict if multiple fields, single value if one
    """
    try:
        obj = model_class.objects.get(id=obj_id)
        if isinstance(field_names, (list, tuple)):
            return {field: getattr(obj, field, "-") for field in field_names}
        return getattr(obj, field_names, "-")
    except ObjectDoesNotExist:
        if isinstance(field_names, (list, tuple)):
            return {field: "-" for field in field_names}
        return "-"
    

# utils.py
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files.base import ContentFile

def generate_barcode_image(data_string: str, filename: str):
    """
    Generate a barcode image from a string and return a ContentFile and filename.
    
    :param data_string: String to encode into barcode.
    :param filename: Desired base filename (without extension).
    :return: (ContentFile, filename_with_extension)
    """
    code128 = barcode.get_barcode_class('code128')
    barcode_img = code128(data_string, writer=ImageWriter())
    buffer = BytesIO()
    barcode_img.write(buffer)
    return ContentFile(buffer.getvalue()), f"{filename}.png"

import os  # 🔄 Added to handle font path
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter

def generate_custom_barcode_image(brand, details_line, barcode_string, filename):
    # Step 1: Generate barcode image using python-barcode
    code128 = barcode.get_barcode_class('code128')
    barcode_obj = code128(barcode_string, writer=ImageWriter())
    barcode_buffer = BytesIO()
    barcode_obj.write(barcode_buffer, options={"write_text": False})
    barcode_buffer.seek(0)
    barcode_image = Image.open(barcode_buffer)

    # Step 2: Fonts 🔄 Updated to use Roboto from same folder
    try:
        font_path = os.path.join(os.path.dirname(__file__),'fonts', 'Roboto-Regular.ttf')  # 🔄
        font_large = ImageFont.truetype(font_path, 25)  # 🔄
        font_small = ImageFont.truetype(font_path, 20)  # 🔄
    except:
        font_large = font_small = ImageFont.load_default()

    # Step 3: Measure text heights
    brand_height = font_large.getbbox(brand)[3]
    details_height = font_small.getbbox(details_line)[3]
    barcode_text_height = font_small.getbbox(barcode_string)[3]

    spacing = 10  # Vertical padding between lines

    # Step 4: Total image height
    total_height = (
        spacing + brand_height +
        spacing + details_height +
        spacing + barcode_image.height +
        spacing + barcode_text_height +
        spacing
    )

    # Step 5: Final image creation
    width = max(barcode_image.width, 400)
    final_image = Image.new('RGB', (width, total_height), "white")
    draw = ImageDraw.Draw(final_image)

    y_offset = spacing

    # Draw brand (line 1)
    brand_width = draw.textlength(brand, font=font_large)
    draw.text(((width - brand_width) / 2, y_offset), brand, fill="black", font=font_large)
    y_offset += brand_height + spacing

    # Draw details (line 2)
    details_width = draw.textlength(details_line, font=font_small)
    draw.text(((width - details_width) / 2, y_offset), details_line, fill="black", font=font_small)
    y_offset += details_height + spacing

    # Paste barcode image (line 3)
    final_image.paste(barcode_image, ((width - barcode_image.width) // 2, y_offset))
    y_offset += barcode_image.height + spacing

    # Draw barcode string (line 4)
    barcode_text_width = draw.textlength(barcode_string, font=font_small)
    draw.text(((width - barcode_text_width) / 2, y_offset), barcode_string, fill="black", font=font_small)

    # Step 6: Save final image to in-memory file
    output_buffer = BytesIO()
    final_image.save(output_buffer, format="PNG")
    return ContentFile(output_buffer.getvalue()), f"{filename}.png"


#  def generate_custom_barcode_image(brand, details_line, barcode_string, filename):
#     # Step 1: Generate barcode image using python-barcode
#     code128 = barcode.get_barcode_class('code128')
#     barcode_obj = code128(barcode_string, writer=ImageWriter())
#     barcode_buffer = BytesIO()
#     barcode_obj.write(barcode_buffer, options={"write_text": False})
#     barcode_buffer.seek(0)
#     barcode_image = Image.open(barcode_buffer)

#     # Step 2: Create new image with space for text
#     width = max(barcode_image.width, 400)
#     total_height = barcode_image.height + 100

#     final_image = Image.new('RGB', (width, total_height), "white")
#     draw = ImageDraw.Draw(final_image)

#     try:
#         font_large = ImageFont.truetype("arial.ttf", 20)
#         font_small = ImageFont.truetype("arial.ttf", 16)
#     except:
#         font_large = font_small = ImageFont.load_default()

#     # Draw brand (line 1)
#     y_offset = 10
#     draw.text(((width - draw.textlength(brand, font=font_large)) / 2, y_offset), brand, fill="black", font=font_large)

#     # Draw label line (line 2)
#     y_offset += 25
#     draw.text(((width - draw.textlength(details_line, font=font_small)) / 2, y_offset), details_line, fill="black", font=font_small)

#     # Paste barcode (line 3)
#     y_offset += 25
#     final_image.paste(barcode_image, ((width - barcode_image.width) // 2, y_offset))

#     # Draw barcode string (line 4)
#     y_offset += barcode_image.height + 5
#     draw.text(((width - draw.textlength(barcode_string, font=font_small)) / 2, y_offset), barcode_string, fill="black", font=font_small)

#     # Save final image
#     output_buffer = BytesIO()
#     final_image.save(output_buffer, format="PNG")
#     return ContentFile(output_buffer.getvalue()), f"{filename}.png" 


# views.py for barcode
# from .utils import generate_barcode_image
# from django.http import HttpResponse

# def barcode_preview(request):
#     content, filename = generate_barcode_image("TEST_1234", "test_barcode")
#     return HttpResponse(content, content_type="image/png")


# utils.py
from django.db import transaction
from django.db.models import IntegerField
from django.db.models.functions import Substr, Cast

def generate_sequential_number(model_class, field_name='order_number', prefix='', padding=4):
    """
    Generate the next sequential number for a model field with a prefix and zero-padding.

    Args:
        model_class: Django model class to query.
        field_name: The model field to check for last number.
        prefix: Prefix string, e.g. 'PO', 'ORD'.
        padding: Number of digits for zero-padding.

    Returns:
        New sequential number string, e.g. 'PO0005'
    """

    prefix_len = len(prefix)

    with transaction.atomic():
        # Lock rows to avoid race conditions when multiple calls happen concurrently
        last_obj = (
            model_class.objects
            .select_for_update()
            .filter(**{f"{field_name}__startswith": prefix})
            .annotate(
                # Extract substring after prefix and cast to int
                num_part=Cast(
                    Substr(field_name, prefix_len + 1), 
                    IntegerField()
                )
            )
            .order_by('-num_part')
            .first()
        )

        if last_obj and getattr(last_obj, 'num_part'):
            last_num = getattr(last_obj, 'num_part')
        else:
            last_num = 0

        next_num = last_num + 1
        return f"{prefix}{str(next_num).zfill(padding)}"



# class PurchaseOrder(models.Model):
#     # your fields...
#     order_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

#     def save(self, *args, **kwargs):
#         if not self.order_number:
#             self.order_number = generate_sequential_number(PurchaseOrder, field_name='order_number', prefix='ORD', padding=4)

#         # continue with barcode generation, etc...
#         super().save(*args, **kwargs)