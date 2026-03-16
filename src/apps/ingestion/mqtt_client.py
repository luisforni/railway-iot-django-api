import json
import logging
import threading

import paho.mqtt.client as mqtt
from django.conf import settings

logger = logging.getLogger(__name__)

_client: mqtt.Client | None = None
_lock = threading.Lock()

def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(settings.MQTT_TOPIC, qos=0)
        logger.info("MQTT connected — subscribed to %s", settings.MQTT_TOPIC)
    else:
        logger.error("MQTT connection failed: reason_code=%s", reason_code)

def _on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        logger.warning("MQTT unexpected disconnect: reason_code=%s", reason_code)

def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("MQTT bad payload on %s: %s", msg.topic, exc)
        return

    try:
        from apps.tasks.ingest import persist_reading
        persist_reading.delay(payload)
    except Exception as exc:
        logger.error("Failed to enqueue persist_reading: %s", exc)

def start() -> None:
    global _client

    with _lock:
        if _client is not None:
            return

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = _on_connect
        client.on_disconnect = _on_disconnect
        client.on_message = _on_message

        if settings.MQTT_USERNAME:
            client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        try:
            client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        except Exception as exc:
            logger.error("MQTT connect error (%s:%s): %s", settings.MQTT_HOST, settings.MQTT_PORT, exc)
            return

        thread = threading.Thread(target=client.loop_forever, daemon=True, name="mqtt-loop")
        thread.start()
        _client = client
        logger.info("MQTT client started — broker=%s:%s", settings.MQTT_HOST, settings.MQTT_PORT)
