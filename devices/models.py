from django.db import models
from accounts.models import Company, Address


class Device(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ]
    serial_number = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=4370)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="offline")
    
    def __str__(self):
        return f"{self.serial_number} : {self.address}"

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
        dev = self.device.serial_number if self.device else "Unknown Device"
        return f"{dev} - {self.status} - {self.timestamp}"
