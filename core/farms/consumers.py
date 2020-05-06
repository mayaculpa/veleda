import json

from channels.generic.websocket import WebsocketConsumer

from farms.serializers import WsMqttMessageSerializer
from farms.models import Coordinator


class CoordinatorConsumer(WebsocketConsumer):
    """Handle MQTT messages being sent to and from coordinators"""

    def handle_mqtt_message(self, data):
        pass

    def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            self.close()
        else:
            coordinator = Coordinator.objects.get(
                pk=self.scope["url_route"]["kwargs"]["pk"]
            )
            if coordinator.channel_name:
                self.channel_layer.send(
                    coordinator.channel_name, {"type": "coordinator.disconnect"}
                )
            coordinator.channel_name = self.channel_name
            coordinator.save()

            self.accept()

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            msg_type = data.pop("type")
            if msg_type == "mqtt-message":
                self.handle_mqtt_message(data)
            else:
                error = {"error": f"Unknown message type: {msg_type}"}
                self.send(json.dumps(error))
        except json.decoder.JSONDecodeError:
            error = {"error": "Invalid data"}
            self.send(json.dumps(error))
            self.close()

    def coordinator_disconnect(self):
        self.close()
