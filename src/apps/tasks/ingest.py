import logging
import re
from datetime import datetime, timezone

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import connection

logger = logging.getLogger(__name__)

VALID_METRICS = {"temperature", "vibration", "rpm", "brake-pressure", "load-weight"}
METRIC_BOUNDS = {
    "temperature":    (-50.0, 200.0),
    "vibration":      (0.0, 100.0),
    "rpm":            (0.0, 5000.0),
    "brake-pressure": (0.0, 20.0),
    "load-weight":    (0.0, 200_000.0),
}
_SAFE_ID_RE = re.compile(r"^[\w\-]{1,64}$")

def _validate_payload(payload: dict) -> dict | None:
    required = ("device_id", "zone", "metric", "value", "timestamp")
    for field in required:
        if field not in payload:
            logger.warning("MQTT payload missing field '%s': %s", field, payload)
            return None

    device_id = str(payload["device_id"])
    zone = str(payload["zone"])
    metric = str(payload["metric"])

    if not _SAFE_ID_RE.match(device_id):
        logger.warning("MQTT payload invalid device_id: %s", device_id)
        return None

    if not _SAFE_ID_RE.match(zone):
        logger.warning("MQTT payload invalid zone: %s", zone)
        return None

    if metric not in VALID_METRICS:
        logger.warning("MQTT payload unknown metric: %s", metric)
        return None

    try:
        value = float(payload["value"])
    except (TypeError, ValueError):
        logger.warning("MQTT payload non-numeric value: %s", payload["value"])
        return None

    low, high = METRIC_BOUNDS[metric]
    if not (low <= value <= high):
        logger.warning("MQTT payload value out of bounds for %s: %s", metric, value)
        return None

    try:
        ts = str(payload["timestamp"])
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        logger.warning("MQTT payload invalid timestamp: %s", payload.get("timestamp"))
        return None

    return {
        "device_id": device_id,
        "zone": zone,
        "metric": metric,
        "value": value,
        "unit": str(payload.get("unit", ""))[:20],
        "timestamp": ts,
    }

@shared_task(bind=True, max_retries=3, default_retry_delay=2)
def persist_reading(self, payload: dict):
    clean = _validate_payload(payload)
    if clean is None:
        return

    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sensor_readings (time, device_id, zone, metric, value, unit)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    clean["timestamp"],
                    clean["device_id"],
                    clean["zone"],
                    clean["metric"],
                    clean["value"],
                    clean["unit"],
                ],
            )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "telemetry",
            {"type": "telemetry.message", "data": clean},
        )

        from .alert_rules import check_threshold_alert
        check_threshold_alert.delay(clean)

    except Exception as exc:
        logger.error(
            "persist_reading failed for %s/%s: %s",
            payload.get("device_id"),
            payload.get("metric"),
            exc,
        )
        raise self.retry(exc=exc)
