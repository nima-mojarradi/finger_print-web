from django.urls import path
from .views import DeviceListView, DeviceCreateView, DeviceUpdateView, DeviceDeleteView, DeviceLogListView

urlpatterns = [
    path("", DeviceListView.as_view(), name="device-list"),
    path("create/", DeviceCreateView.as_view(), name="device-create"),
    path("<int:pk>/edit/", DeviceUpdateView.as_view(), name="device-edit"),
    path("<int:pk>/delete/", DeviceDeleteView.as_view(), name="device-delete"),
    path("logs/", DeviceLogListView.as_view(), name="device-logs"),

]
