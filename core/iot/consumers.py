import json

import channels_graphql_ws
from channels.generic.websocket import WebsocketConsumer

from iot.serializers import ControllerMessageSerializer
from iot.models import (
    ControllerMessage,
    ControllerTask,
    DataPoint,
    PeripheralComponent,
)
from core.schema import schema as graphql_schema


class ControllerConsumer(WebsocketConsumer):
    """Handle JSON messages being sent to and from controllers"""

    class InvalidData(Exception):
        pass

    def handle_errors(self, data):
        """Handle errors sent by the controller. Currently only prints them."""
        # print(data)

    def handle_register(self, message: ControllerMessage):
        """Handle register messages"""

        peripheral_commands = PeripheralComponent.objects.commands_from_register(
            message.to_peripheral_register(), message.controller_id
        )
        self.send_peripheral_commands(
            {"commands": peripheral_commands, "request_id": message.request_id}
        )
        task_commands = ControllerTask.objects.commands_from_register(
            message.to_task_register(), message.controller_id
        )
        self.send_controller_task_commands(
            {"commands": task_commands, "request_id": message.request_id}
        )

    def handle_message(self, json_message, controller):
        """Handle messages sent from the controller"""

        serializer = ControllerMessageSerializer(
            data={
                "message": json_message,
                "controller": controller,
                "request_id": json_message.pop("request_id", ""),
            }
        )
        if not serializer.is_valid():
            raise self.InvalidData(str(serializer.errors))
        message: ControllerMessage = serializer.save()

        # Handle the different message types
        try:
            if data := message.to_telemetry():
                DataPoint.objects.from_telemetry(data)
            elif data := message.to_errors():
                self.handle_errors(data)
            elif message.is_register_type():
                self.handle_register(message)
            elif message.is_result_type():
                if data := message.to_peripheral_results():
                    PeripheralComponent.objects.from_results(data)
                if data := message.to_task_results():
                    ControllerTask.objects.from_results(data)
            elif message.is_system_type():
                pass
            elif message.is_command_type():
                raise self.InvalidData("Command message type only sent to controller")
            else:
                raise self.InvalidData(f"Unkown message type: {message.get_type()}")
        except ValueError as err:
            raise self.InvalidData(err) from err

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
            self.handle_message(data, self.scope["controller"].pk)
        except json.decoder.JSONDecodeError:
            self.disconnect_controller({"errors": "Invalid JSON data"})
        except self.InvalidData as err:
            self.disconnect_controller({"errors": str(err.args)})

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


class GraphqlConsumer(channels_graphql_ws.GraphqlWsConsumer):
    """Channels WebSocket consumer which provides GraphQL API."""
    schema = graphql_schema
    
    async def connect(self):
        """If the user is not authenticated, close the connection."""
        if not self.scope["user"].is_authenticated:
            await self.close()
        else:
            await super().connect()
