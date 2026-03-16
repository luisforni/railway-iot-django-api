import logging
import re

from django.db import connection
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Device, Zone
from .serializers import DeviceSerializer, ZoneSerializer

logger = logging.getLogger(__name__)

VALID_METRICS = {"temperature", "vibration", "rpm", "brake-pressure", "load-weight"}
_SAFE_ID_RE = re.compile(r"^[\w\-]{1,64}$")

def _validate_id(value: str, field: str) -> str:
    if not _SAFE_ID_RE.match(value):
        raise ValidationError({field: "Invalid format."})
    return value

class SensorReadingListView(APIView):

    def get(self, request):
        device_id = request.query_params.get("device_id")
        zone = request.query_params.get("zone")
        metric = request.query_params.get("metric")
        since = request.query_params.get("since")

        try:
            limit = min(int(request.query_params.get("limit", 200)), 1000)
        except (ValueError, TypeError):
            raise ValidationError({"limit": "Must be an integer."})

        if device_id:
            device_id = _validate_id(device_id, "device_id")
        if zone:
            zone = _validate_id(zone, "zone")
        if metric and metric not in VALID_METRICS:
            raise ValidationError({"metric": f"Must be one of {sorted(VALID_METRICS)}."})

        sql = """
            SELECT time, device_id, zone, metric, value, unit, anomaly
            FROM sensor_readings
            WHERE 1=1
        """
        params: list = []

        if device_id:
            sql += " AND device_id = %s"
            params.append(device_id)
        if zone:
            sql += " AND zone = %s"
            params.append(zone)
        if metric:
            sql += " AND metric = %s"
            params.append(metric)
        if since:
            sql += " AND time >= %s"
            params.append(since)

        sql += " ORDER BY time DESC LIMIT %s"
        params.append(limit)

        with connection.cursor() as cur:
            cur.execute(sql, params)
            cols = [col[0] for col in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]

        for row in rows:
            if hasattr(row["time"], "isoformat"):
                row["time"] = row["time"].isoformat()

        return Response(rows)

class SensorReadingLatestView(APIView):

    def get(self, request):
        zone = request.query_params.get("zone")

        if zone:
            zone = _validate_id(zone, "zone")
            sql = """
                SELECT DISTINCT ON (device_id, metric)
                    time, device_id, zone, metric, value, unit, anomaly
                FROM sensor_readings
                WHERE zone = %s
                ORDER BY device_id, metric, time DESC
            """
            params = [zone]
        else:
            sql = """
                SELECT DISTINCT ON (device_id, metric)
                    time, device_id, zone, metric, value, unit, anomaly
                FROM sensor_readings
                ORDER BY device_id, metric, time DESC
            """
            params = []

        with connection.cursor() as cur:
            cur.execute(sql, params)
            cols = [col[0] for col in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]

        for row in rows:
            if hasattr(row["time"], "isoformat"):
                row["time"] = row["time"].isoformat()

        return Response(rows)

class ZoneListView(APIView):

    def get(self, request):
        return Response(ZoneSerializer(Zone.objects.all(), many=True).data)

class DeviceListView(APIView):

    def get(self, request):
        zone = request.query_params.get("zone")
        qs = Device.objects.select_related("zone").all()
        if zone:
            zone = _validate_id(zone, "zone")
            qs = qs.filter(zone__name=zone)
        return Response(DeviceSerializer(qs, many=True).data)
