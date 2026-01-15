import json

from channels.generic.websocket import AsyncWebsocketConsumer


class MoodUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("mood_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("mood_updates", self.channel_name)

    async def mood_update(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
