from django.db import models
from accounts.models import CustomUser

class AttendanceEvent(models.Model):
    class EventType(models.TextChoices):
        CHECK_IN = "in", "Check In"
        CHECK_OUT = "out", "Check Out"

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="attendance_events")
    event_type = models.CharField(max_length=10, choices=EventType.choices)
    timestamp = models.DateTimeField()
    verified_by = models.CharField(max_length=50, default="fingerprint")
    device_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.get_event_type_display()} @ {self.timestamp}"
