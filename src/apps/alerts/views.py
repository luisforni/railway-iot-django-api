import logging
import re

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alert
from .serializers import AlertSerializer

logger = logging.getLogger(__name__)

VALID_SEVERITIES = {"low", "medium", "high", "critical"}
_SAFE_ID_RE = re.compile(r"^[\w\-]{1,64}$")

class AlertListView(APIView):

    def get(self, request):
        qs = Alert.objects.all()

        severity = request.query_params.get("severity")
        zone = request.query_params.get("zone")
        device_id = request.query_params.get("device_id")
        acknowledged = request.query_params.get("acknowledged")

        if severity:
            if severity not in VALID_SEVERITIES:
                raise ValidationError({"severity": f"Must be one of {sorted(VALID_SEVERITIES)}."})
            qs = qs.filter(severity=severity)

        if zone:
            if not _SAFE_ID_RE.match(zone):
                raise ValidationError({"zone": "Invalid format."})
            qs = qs.filter(zone=zone)

        if device_id:
            if not _SAFE_ID_RE.match(device_id):
                raise ValidationError({"device_id": "Invalid format."})
            qs = qs.filter(device_id=device_id)

        if acknowledged is not None:
            qs = qs.filter(acknowledged=acknowledged.lower() == "true")

        qs = qs[:200]
        return Response(AlertSerializer(qs, many=True).data)

class AlertDetailView(APIView):

    def patch(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        allowed_fields = {"acknowledged"}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        if not data:
            return Response(
                {"detail": "Only 'acknowledged' field can be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AlertSerializer(alert, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.warning(
                "Alert %d acknowledged by user %s",
                pk,
                getattr(request.user, "username", "anonymous"),
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
