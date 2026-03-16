import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

THRESHOLDS: dict[str, dict] = {
    "temperature":    {"warning": 70.0,   "critical": 82.0},
    "vibration":      {"warning": 7.0,    "critical": 9.0},
    "rpm":            {"warning": 1600.0, "critical": 1750.0},
    "brake-pressure": {"warning": 7.0,    "critical": 7.8},
    "load-weight":    {"warning": 72000,  "critical": 78000},
}

@shared_task
def check_threshold_alert(payload: dict):
    metric = payload.get("metric")
    value = payload.get("value")

    if metric not in THRESHOLDS or value is None:
        return

    thresholds = THRESHOLDS[metric]

    if value >= thresholds["critical"]:
        severity = "critical"
        threshold = thresholds["critical"]
    elif value >= thresholds["warning"]:
        severity = "high"
        threshold = thresholds["warning"]
    else:
        return

    from apps.alerts.models import Alert

    alert = Alert.objects.create(
        device_id=payload["device_id"],
        zone=payload["zone"],
        metric=metric,
        value=value,
        threshold=threshold,
        severity=severity,
        message=(
            f"{metric} reading {value:.2f} exceeded {severity} threshold "
            f"{threshold} on device {payload['device_id']} (zone: {payload['zone']})"
        ),
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "alerts",
        {
            "type": "alert.message",
            "data": {
                "id": alert.id,
                "device_id": alert.device_id,
                "zone": alert.zone,
                "metric": alert.metric,
                "value": alert.value,
                "severity": alert.severity,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
            },
        },
    )
    logger.warning("Alert created: %s", alert)
