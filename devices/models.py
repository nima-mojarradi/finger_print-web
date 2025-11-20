from django.db import models
from accounts.models import Company

STATUS_CHOICES = [
    ('online', 'Online'),
    ('offline', 'Offline'),
    ('error', 'Error'),
]

class Device(models.Model):
    serial_number = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=4370)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="offline")
    
    def __str__(self):
        return f"{self.company} : {self.longitude}, {self.latitude}"

# alipoor 09153870790

class DeviceLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, related_name='logs', null=True, blank=True)
    status = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.IntegerField(null=True, blank=True)
    message = models.CharField(max_length=255, null=True, blank=True)
    extra_data = models.JSONField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.serial_number} - {self.status} - {self.timestamp}"
