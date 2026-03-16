from rest_framework import serializers
from .models import Device, Zone

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["id", "name", "description", "created_at"]

class DeviceSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = Device
        fields = ["id", "device_id", "zone_name", "device_type", "active", "created_at"]
