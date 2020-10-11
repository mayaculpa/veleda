import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from farms.serializers import ControllerMessageSerializer
from farms.models import ControllerComponent


class ControllerConsumer(WebsocketConsumer):
    """Handle JSON messages being sent to and from controllers"""

    controller_id = None

    def handle_message(self, message):
        serializer = ControllerMessageSerializer(
            data={
                "message": message,
                "controller": self.scope["controller"].id,
            }
        )
        if not serializer.is_valid():
            self.send(json.dumps({"errors": serializer.errors["message"]}))
            self.close()
        else:
            serializer.save()

    def connect(self):
        controller = self.scope["controller"]
        if controller:
            if controller.channel_name:
                async_to_sync(self.channel_layer.send)(
                    controller.channel_name, {"type": "controller.disconnect"}
                )
            controller.channel_name = self.channel_name
            controller.save()

            self.accept()
        else:
            self.close()

    def disconnect(self, code):
        """On disconnect clear the channel name to its WebSocket"""
        if controller := self.scope.get("controller"):
            controller.channel_name = ""
            controller.save()

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            self.handle_message(data)
        except json.decoder.JSONDecodeError:
            error = {"error": "Invalid data"}
            self.send(json.dumps(error))
            self.close()

    def controller_disconnect(self, event):
        self.close()

    def command_controller(self, message):
        self.send(json.dumps(message["message"]))
