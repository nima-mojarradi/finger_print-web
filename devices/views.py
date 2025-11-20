from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DeviceSerializer
from .models import Device, DeviceLog


class ManageDevices(APIView):

    def get(self, request):
        devices = Device.objects.all()
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            device = serializer.save()
            DeviceLog.objects.create(
                device=device,
                status="created",
                message="Device created"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request):
        device_id = request.query_params.get("id")
        if not device_id:
            return Response({"error": "id parameter is required"}, status=400)
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=404)
        serializer = DeviceSerializer(device, data=request.data, partial=True)
        if serializer.is_valid():
            updated_device = serializer.save()
            DeviceLog.objects.create(
                device=updated_device,
                status="updated",
                message="Device updated",
                extra_data=request.data
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


    def delete(self, request):
        device_id = request.query_params.get("id")
        if not device_id:
            return Response({"error": "id parameter is required"}, status=400)
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=404)
        DeviceLog.objects.create(
            device=device,
            status="deleted",
            message="Device deleted"
        )
        device.delete()
        return Response({"message": "Device deleted"}, status=200)

