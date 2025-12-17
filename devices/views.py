from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .models import Device, DeviceLog
from .forms import DeviceForm
from django.views.generic import ListView
from django.contrib import messages


class DeviceLogListView(ListView):
    model = DeviceLog
    template_name = "device_logs.html"
    context_object_name = "logs"
    ordering = ['-timestamp']
    paginate_by = 30

class DeviceListView(View):
    def get(self, request):
        devices = Device.objects.filter(is_active=True)
        return render(request, "device_list.html", {"devices": devices})

class DeviceCreateView(View):
    def get(self, request):
        form = DeviceForm()
        return render(request, "device_form.html", {"form": form})

    def post(self, request):
        form = DeviceForm(request.POST)
        if form.is_valid():
            device = form.save()
            DeviceLog.objects.create(
                device=device,
                status="created",
                message="Device created"
            )
            return redirect("device-list")
        return render(request, "device_form.html", {"form": form})

class DeviceUpdateView(View):
    def get(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        form = DeviceForm(instance=device)
        return render(request, "device_form.html", {"form": form, "device": device})

    def post(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            updated_device = form.save()
            DeviceLog.objects.create(
                device=updated_device,
                status="updated",
                message="Device updated",
                extra_data=request.POST
            )
            return redirect("device-list")
        return render(request, "device_form.html", {"form": form, "device": device})


class DeviceDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.roles != "super_admin":
            return JsonResponse({"error": "فقط سوپر ادمین می‌تواند حذف کند."}, status=403)

        device = get_object_or_404(Device, pk=pk, is_active=True)

        device.is_active = False
        device.deleted_at = timezone.now()
        device.save()

        return JsonResponse({
            "success": True,
            "message": f"دستگاه «{device.serial_number}» با موفقیت غیرفعال شد."
        })
    

class ArchivedDeviceListView(LoginRequiredMixin, View):
    template_name = 'archived_devices.html'

    def get(self, request):
        devices = Device.objects.filter(is_active=False)
        return render(request, self.template_name, {'devices': devices})
    

class ReactivateDeviceView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.roles != "super_admin":
            messages.error(request, "فقط سوپر ادمین می‌تواند دستگاه را بازیابی کند.")
            return redirect('device-list')

        device = get_object_or_404(Device, pk=pk, is_active=False)

        device.is_active = True
        device.deleted_at = None
        device.save()

        messages.success(request, f"دستگاه «{device.serial_number}» با موفقیت بازیابی شد.")
        return redirect('device-list')  