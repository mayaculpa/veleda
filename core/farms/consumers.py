import json
import uuid
from typing import Union, Type

from channels.generic.websocket import WebsocketConsumer
from rest_framework.utils.serializer_helpers import ReturnDict

from farms.serializers import ControllerMessageSerializer
from farms.models import (
    ControllerMessage,
    ControllerTask,
    DataPoint,
    DataPointType,
    PeripheralComponent,
    PeripheralComponentManager,
)


class ControllerConsumer(WebsocketConsumer):
    """Handle JSON messages being sent to and from controllers"""

    class InvalidData(Exception):
        pass

    def handle_errors(self, data):
        """Handle errors sent by the controller. Currently only prints them."""
        # print(data)

    def handle_register(self, data):
        """Handle register messages"""
        # print(data)

    def handle_message(self, message, controller):
        """Handle messages sent from the controller"""

        serializer = ControllerMessageSerializer(
            data={"message": message, "controller": controller}
        )
        if not serializer.is_valid():
            raise self.InvalidData(serializer.errors["message"])
        message: Type[ControllerMessage] = serializer.save()

        # Handle the different message types
        if data := message.to_telemetry():
            DataPoint.objects.from_telemetry(data)
        elif data := message.to_errors():
            self.handle_errors(data)
        elif data := message.to_register():
            self.handle_register(data)
        elif message.is_result_type():
            if data := message.to_peripheral_results():
                PeripheralComponent.objects.from_results(data)
            if data := message.to_task_results():
                ControllerTask.objects.from_results(data)
        elif message.is_command_type():
            raise self.InvalidData("Command message type only sent to controller")
        else:
            raise self.InvalidData(f"Unkown message type: {message.get_type()}")

    def connect(self):
        controller = self.scope["controller"]
        if controller:
            controller.channel_name = self.channel_name
            controller.save()
            self.accept()
        else:
            self.close()

    def disconnect_controller(self, event) -> None:
        """Closes the WebSocket connection"""

        if errors := event.get("errors", ""):
            # print(f"Disconnect errors: {errors}")
            self.send(json.dumps({"errors": errors}))
        self.close()

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            self.handle_message(data, self.scope["controller"].id)
        except json.decoder.JSONDecodeError:
            self.disconnect_controller({"errors": "Invalid JSON data"})
        except self.InvalidData as err:
            self.disconnect_controller({"errors": err.args})

    def send_peripheral_commands(self, message):
        """Send peripheral commands to the controller"""

        request = ControllerMessage.to_command_message(
            peripheral_commands=message["commands"], request_id=message["request_id"]
        )
        self.send(json.dumps(request))

    def send_controller_task_commands(self, message):
        """Send task commands to the controller"""

        request = ControllerMessage.to_command_message(
            task_commands=message["commands"], request_id=message["request_id"]
        )
        self.send(json.dumps(request))
