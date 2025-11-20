from django.urls import path
from .views import FingerprintAttendanceView, AttendanceReportView

urlpatterns = [
    path("fingerprint/", FingerprintAttendanceView.as_view(), name="fingerprint-attendance"),
    path("report/", AttendanceReportView.as_view(), name="attendance-report-download"),
]
