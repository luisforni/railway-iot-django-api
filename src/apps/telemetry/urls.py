from django.urls import path
from . import views

urlpatterns = [
    path("readings/", views.SensorReadingListView.as_view(), name="reading-list"),
    path("readings/latest/", views.SensorReadingLatestView.as_view(), name="reading-latest"),
    path("zones/", views.ZoneListView.as_view(), name="zone-list"),
    path("devices/", views.DeviceListView.as_view(), name="device-list"),
]
