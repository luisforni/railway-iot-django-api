import sys
from django.apps import AppConfig

class IngestionConfig(AppConfig):
    name = "apps.ingestion"
    verbose_name = "MQTT Ingestion"

    def ready(self):
        skip_commands = {"migrate", "makemigrations", "collectstatic", "test", "shell"}
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        from . import mqtt_client
        mqtt_client.start()
