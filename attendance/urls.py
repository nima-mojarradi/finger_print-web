from django.urls import path
from .views import FingerprintAttendanceView, AttendanceReportView

urlpatterns = [
    path('fingerprint-attendance/', FingerprintAttendanceView.as_view(), name='fingerprint-attendance'),
    path('attendance-report/', AttendanceReportView.as_view(), name='attendance-report'),
]
