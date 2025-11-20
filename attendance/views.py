import datetime, csv
from io import BytesIO
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.utils.timezone import is_aware
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.models import Fingerprint
from .models import AttendanceEvent
from .serializers import AttendanceEventSerializer


class FingerprintAttendanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        fingerprint_id = request.data.get("finger_id")
        device_id = request.data.get("device_id")

        if not fingerprint_id:
            return Response({"error": "finger_id is required"}, status=400)

        try:
            fingerprint = Fingerprint.objects.get(id=fingerprint_id)
        except Fingerprint.DoesNotExist:
            return Response({"error": "Fingerprint not recognized"}, status=404)

        user = fingerprint.user
        last_event = AttendanceEvent.objects.filter(user=user).order_by('-timestamp').first()
        now = timezone.now()

        if last_event and last_event.event_type == "in":
            time_diff = now - last_event.timestamp
            if time_diff <= timedelta(hours=24):
                event_type = "out"
            else:
                event_type = "out"
                now = last_event.timestamp
        else:
            event_type = "in"

        event = AttendanceEvent.objects.create(
            user=user,
            event_type=event_type,
            verified_by="fingerprint",
            device_id=device_id,
            timestamp=now
        )

        return Response({
            "message": f"{event_type.capitalize()} recorded successfully",
            "user": f"{user.first_name} {user.last_name}",
            "timestamp": event.timestamp,
            "event_type": event.event_type,
        }, status=201)
    
class AttendanceReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, user, start_date=None, end_date=None, specific_user=None):
        if user.roles == "user":
            qs = AttendanceEvent.objects.filter(user=user)

        elif user.roles == "normal_admin":
            qs = AttendanceEvent.objects.filter(user__company=user.company)

            if specific_user:
                qs = qs.filter(user__id=specific_user, user__company=user.company)

        elif user.roles == "super_admin":
            qs = AttendanceEvent.objects.all()

            if specific_user:
                qs = qs.filter(user__id=specific_user)

        else:
            return None

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return qs

    def get(self, request):
        return self._handle_request(request)

    def post(self, request):
        return self._handle_request(request)

    def _handle_request(self, request):
        user = request.user

        start_date = request.query_params.get("start_date") or request.data.get("start_date")
        end_date = request.query_params.get("end_date") or request.data.get("end_date")
        specific_user = request.query_params.get("user_id") or request.data.get("user_id")

        try:
            if start_date:
                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        queryset = self.get_queryset(user, start_date, end_date, specific_user)

        if queryset is None:
            return Response({"error": "Invalid role"}, status=403)

        export_type = (
            request.query_params.get("export") 
            or request.data.get("export") 
            or "json"
        ).lower()

        if export_type == "json":
            serializer = AttendanceEventSerializer(queryset, many=True)
            return Response(serializer.data, status=200)

        file_buffer = BytesIO()
        filename = f"attendance_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if export_type == "xlsx":
            wb = Workbook()
            ws = wb.active
            ws.title = "Attendance Report"

            ws.append(["User", "Event Type", "Timestamp", "Date", "Verified By", "Device ID"])

            for event in queryset:
                ts = event.timestamp
                if is_aware(ts):
                    ts = ts.replace(tzinfo=None)

                ws.append([
                    str(event.user),
                    event.get_event_type_display(),
                    ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "",
                    event.date.strftime("%Y-%m-%d") if event.date else "",
                    str(event.verified_by or ""),
                    event.device_id or "",
                ])

            for col in ws.columns:
                max_len = max(len(str(cell.value)) for cell in col if cell.value) + 2
                ws.column_dimensions[get_column_letter(col[0].column)].width = max_len

            wb.save(file_buffer)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename += ".xlsx"
            file_buffer.seek(0)

        elif export_type == "csv":
            writer = csv.writer(file_buffer)
            writer.writerow(["User", "Event Type", "Timestamp", "Date", "Verified By", "Device ID"])

            for event in queryset:
                ts = event.timestamp
                if is_aware(ts):
                    ts = ts.replace(tzinfo=None)

                writer.writerow([
                    str(event.user),
                    event.get_event_type_display(),
                    ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "",
                    event.date.strftime("%Y-%m-%d") if event.date else "",
                    str(event.verified_by or ""),
                    event.device_id or "",
                ])

            content_type = "text/csv"
            filename += ".csv"
            file_buffer.seek(0)

        else:
            return Response({"error": "Invalid export type"}, status=400)

        response = HttpResponse(file_buffer, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


