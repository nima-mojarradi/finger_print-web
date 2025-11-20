from django.urls import include,path
from .views import ManageDevices


urlpatterns = [
    path('devices/', ManageDevices.as_view())
]