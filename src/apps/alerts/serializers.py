from rest_framework import serializers
from .models import Alert

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id", "device_id", "zone", "metric", "value",
            "threshold", "severity", "message",
            "acknowledged", "created_at",
        ]
        read_only_fields = [
            "id", "device_id", "zone", "metric", "value",
            "threshold", "severity", "message", "created_at",
        ]
