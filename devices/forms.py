from django import forms
from .models import Device

class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["serial_number", "ip_address", "port", "is_active", "status", "address"]
        widgets = {
            "status": forms.Select(choices=Device.STATUS_CHOICES),
        }
