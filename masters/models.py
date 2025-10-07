from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.utils.text import slugify

# Create your models here.

# ---------------------------------------------------company---------------------------------------------------------------------------

class company_table(models.Model):
    name = models.CharField(max_length=50)
    company_code = models.CharField(max_length=50)
    short_name = models.CharField(max_length=50,null=True)
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    pincode = models.IntegerField()
    state = models.CharField(max_length=50)
    gstin = models.CharField(max_length=50)
    state_code = models.IntegerField()
    country = models.CharField(max_length=50)
    current_fy = models.IntegerField()
    email = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    mobile = models.CharField(max_length=20)
    report_email = models.CharField(max_length=50)
    contact_person_name = models.CharField(max_length=50)
    cp_phone = models.CharField(max_length=20)
    cp_mobile = models.CharField(max_length=20)
    cp_email = models.CharField(max_length=50)
    enc_code = models.CharField(max_length=100)
    uen_code = models.CharField(max_length=50)
    logo = models.CharField(max_length=300)
    logo_small = models.CharField(max_length=100)
    logo_invoice = models.CharField(max_length=100)
    master_id = models.IntegerField()
    facebook= models.URLField(null=True)
    insta= models.URLField(null=True)
    linkedin= models.URLField(null=True)
    twitter= models.URLField(null=True)
    tax_type = models.IntegerField()
    free_shipping_threshold =models.DecimalField(max_digits=20, null=True, decimal_places=2)
    default_shipping_rate = models.DecimalField(max_digits=20, null=True, decimal_places=2)
    delivery_charge = models.IntegerField()
    mode = models.CharField(max_length=50)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "company"


# ---------------------------------------------------financial year---------------------------------------------------------------------------


class financialyear_table(models.Model):
    name = models.CharField(max_length=20,  unique=True,  help_text="e.g. 2024-2025")
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)


    class Meta:
        db_table = "financial_year"

 
# ---------------------------------------------------employee---------------------------------------------------------------------------

class employee_table(models.Model):
    auth_id=models.IntegerField(null=True)
    name=models.CharField(max_length=150,null=True) 
    username=models.CharField(max_length=150)
    email=models.EmailField()
    phone=models.IntegerField(null=True)
    password=models.CharField(max_length=200)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "employee"  


# ---------------------------------------------------category---------------------------------------------------------------------------

class category_table(models.Model):

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_featured = models.IntegerField(default=0)
    sort_order_no = models.IntegerField(default=0, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)  
    created_by = models.IntegerField(default=0)
    updated_by = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(category_table, self).save(*args, **kwargs)

    class Meta:
        db_table = "category"

# ---------------------------------------------------color---------------------------------------------------------------------------

class color_table(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=20, blank=True, null=True)  # Allow blank since we set it automatically
    description = models.CharField(max_length=100) 
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(default=0)
    updated_by = models.IntegerField(default=0)

    class Meta:
        db_table = "color"

    def save(self, *args, **kwargs):
        # Example logic: short_name is first 3 letters uppercase of name
        if not self.short_name:  # Only set if not provided manually
            self.short_name = self.name[:1].upper()

        super().save(*args, **kwargs) 


# ---------------------------------------------------school---------------------------------------------------------------------------

class school_table(models.Model):
    name=models.CharField(max_length=150)
    short_name=models.CharField(max_length=10, unique=True)
    delivery_address= models.CharField(max_length=255,null=True)
    billing_address= models.CharField(max_length=255,null=True)
    pincode=models.CharField(max_length=10, unique=True)
    city_code=models.CharField(max_length=10, unique=True)
    school_code=models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)


    class Meta:
        db_table = "school" 


# ---------------------------------------------------size---------------------------------------------------------------------------

class size_table(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "size" 

    


# ---------------------------------------------------style---------------------------------------------------------------------------

class tm_style_table(models.Model):
    school_id=models.IntegerField(null=True)
    category_id=models.IntegerField(null=True)
    color_ids= models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=50, unique=True)
    style_code=models.CharField(max_length=50, unique=True)
    # short_name=models.CharField(max_length=10, unique=True)
    # is_split_packing=models.IntegerField(null=True)
    # is_top=models.IntegerField(null=True)
    # is_bottom=models.IntegerField(null=True)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "tm_style"

class tx_style_table(models.Model):
    style_id=models.IntegerField(null=True)
    size_id=models.IntegerField(null=True)
    position= models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=150, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True)
    updated_by = models.IntegerField(null=True)

    class Meta:
        db_table = "tx_style" 