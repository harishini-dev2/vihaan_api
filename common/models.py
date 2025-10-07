from django.db import models

# Create your models here.
class session_table(models.Model):
    device_id = models.CharField(max_length=30,null=True)
    employee_id = models.IntegerField()
    auth_id = models.IntegerField()
    fcm_token = models.CharField(max_length=250,null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    timestamp = models.CharField(max_length=50)
    session_token = models.TextField(null=True)
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on=models.DateTimeField()
    updated_on=models.DateTimeField()
    created_by=models.IntegerField(null=True)
    updated_by=models.IntegerField(null=True)

    class Meta:
        db_table="login_session"  