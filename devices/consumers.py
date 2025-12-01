import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DeviceStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("devices_status", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("devices_status", self.channel_name)

    async def device_status_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
