from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Device, DeviceLog
from .forms import DeviceForm
from django.views.generic import ListView



class DeviceLogListView(ListView):
    model = DeviceLog
    template_name = "devices/device_logs.html"
    context_object_name = "logs"
    ordering = ['-timestamp']
    paginate_by = 30

class DeviceListView(View):
    def get(self, request):
        devices = Device.objects.all()
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

class DeviceDeleteView(View):
    def post(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        DeviceLog.objects.create(
            device=device,
            status="deleted",
            message="Device deleted"
        )
        device.delete()
        return redirect("device-list")
