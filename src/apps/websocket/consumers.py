import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

class TelemetryConsumer(AsyncJsonWebsocketConsumer):

    GROUP_NAME = "telemetry"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        logger.debug("WS telemetry client connected: %s", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        logger.debug("WS telemetry client disconnected: %s", self.channel_name)

    async def telemetry_message(self, event):
        await self.send_json(event["data"])

class AlertConsumer(AsyncJsonWebsocketConsumer):

    GROUP_NAME = "alerts"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        logger.debug("WS alerts client connected: %s", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def alert_message(self, event):
        await self.send_json(event["data"])
