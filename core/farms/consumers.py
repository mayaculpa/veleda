import json
import uuid

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from farms.serializers import ControllerMessageSerializer
from farms.models import (
    ControllerMessage,
    DataPoint,
    DataPointType,
    PeripheralComponent,
)


class ControllerConsumer(WebsocketConsumer):
    """Handle JSON messages being sent to and from controllers"""

    def handle_telemetry(self, message):
        if message["name"] == "ReadSensor":
            peripheral_component = PeripheralComponent.objects.get(
                pk=uuid.UUID(message["peripheral"])
            )
            data_points = DataPoint.objects.bulk_create(
                [
                    DataPoint(
                        value=data_point["value"],
                        peripheral_component=peripheral_component,
                        data_point_type=DataPointType.objects.get(
                            pk=uuid.UUID(data_point["data_point_type"])
                        ),
                    )
                    for data_point in message["data_points"]
                ]
            )

            print(data_points)

    def handle_message(self, message, controller):
        serializer = ControllerMessageSerializer(
            data={"message": message, "controller": controller}
        )
        if not serializer.is_valid():
            self.send(json.dumps({"errors": serializer.errors["message"]}))
            self.close()
        else:
            print(serializer.validated_data)
            message_type = serializer.validated_data["message"]["type"]
            if message_type == ControllerMessage.TELEMETRY_TYPE:
                self.handle_telemetry(serializer.validated_data["message"])

            serializer.save()

    def connect(self):
        controller = self.scope["controller"]
        if controller:
            controller.channel_name = self.channel_name
            controller.save()

            self.accept()
        else:
            self.close()

    def disconnect(self, code):
        pass

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            self.handle_message(data, self.scope["controller"].id)
        except json.decoder.JSONDecodeError:
            error = {"error": "Invalid data"}
            self.send(json.dumps(error))
            self.close()

    def controller_disconnect(self, event):
        self.close()

    def command_controller(self, message):
        self.send(json.dumps(message["message"]))

    def send_peripheral_commands(self, message):
        request = ControllerMessage.to_peripheral_message(
            message["commands"], message["request_id"]
        )
        self.send(json.dumps(request))

    def send_controller_task_commands(self, message):
        request = ControllerMessage.to_task_message(
            message["commands"], message["request_id"]
        )
        self.send(json.dumps(request))
