from accounts.models import User
import binascii
import os
import uuid
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from iot.models.site import SiteEntity


class ControllerComponentType(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=255, help_text="The name of this type, e.g., ESP32 or RasberryPi4"
    )
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        blank=False,
        null=True,
        help_text="The user that created the type. Global types have no owner.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return f"{self.name}"


class ControllerComponent(models.Model):
    site_entity = models.OneToOneField(
        SiteEntity,
        primary_key=True,
        related_name="controller_component",
        on_delete=models.CASCADE,
        help_text="Which site entity the component is a part of.",
    )
    component_type = models.ForeignKey(
        ControllerComponentType,
        on_delete=models.CASCADE,
        help_text="The type of which this component is an instance of.",
    )
    channel_name = models.CharField(
        null=False,
        blank=True,
        default="",
        max_length=128,
        help_text="The channel name of the connected WebSocket.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime of creation."
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return f"Controller of {self.site_entity.name}"


def _generate_auth_token():
    """Generates a random token based with a length of CONTROLLER_TOKEN_BYTES """
    return binascii.hexlify(os.urandom(settings.CONTROLLER_TOKEN_BYTES)).decode()


class ControllerAuthToken(models.Model):
    """Token for controller models."""

    key = models.CharField(
        max_length=128, primary_key=True, default=_generate_auth_token
    )
    controller = models.OneToOneField(
        ControllerComponent, related_name="auth_token", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Auth token for {str(self.controller.site_entity.name)}"


class ControllerMessage(models.Model):
    """A message to/from a controller"""

    class Meta:
        unique_together = ["created_at", "controller"]

    COMMAND_TYPE = "cmd"
    ERROR_TYPE = "err"
    REGISTER_TYPE = "reg"
    RESULT_TYPE = "result"
    TELEMETRY_TYPE = "tel"
    SYSTEM_TYPE = "sys"

    TYPES = [
        COMMAND_TYPE,
        ERROR_TYPE,
        REGISTER_TYPE,
        RESULT_TYPE,
        TELEMETRY_TYPE,
        SYSTEM_TYPE,
    ]

    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime when the message was received"
    )
    controller = models.ForeignKey(
        ControllerComponent,
        on_delete=models.CASCADE,
        help_text="The controller associated with the message.",
    )
    message = models.JSONField()

    request_id = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="The ID of the request, to enable tracking requests",
    )

    def is_command_type(self):
        """Checks if it is a command message"""

        return self.message.get("type", "") == self.COMMAND_TYPE

    def is_register_type(self):
        """Checks if it is a register message"""

        return self.message.get("type", "") == self.REGISTER_TYPE

    def is_result_type(self):
        """Checks if it is a result message"""

        return self.message.get("type", "") == self.RESULT_TYPE

    def is_system_type(self):
        """Checks if it is a system message"""

        return self.message.get("type", "") == self.SYSTEM_TYPE

    def to_errors(self) -> Dict:
        """Try to extract errors"""

        if self.message.get("type", "") == self.ERROR_TYPE:
            return self.message
        return {}

    def to_peripheral_commands(self) -> Dict:
        """Try to extract the peripheral commands"""

        if self.message.get("type", "") == self.COMMAND_TYPE:
            return self.message.get("peripheral", {})
        return {}

    def to_task_commands(self) -> Dict:
        """Try to extract the task commands"""

        if self.message.get("type", "") == self.COMMAND_TYPE:
            return self.message.get("task", {})
        return {}

    def to_peripheral_results(self) -> Dict:
        """Try to extract the peripheral results"""

        if self.message.get("type", "") == self.RESULT_TYPE:
            return self.message.get("peripheral", {})
        return {}

    def to_task_results(self) -> Dict:
        """Try to extract the task results"""

        if self.message.get("type", "") == self.RESULT_TYPE:
            return self.message.get("task", {})
        return {}

    def to_peripheral_register(self) -> List[str]:
        """Try to extract the peripheral register message"""

        if self.message.get("type", "") == self.REGISTER_TYPE:
            return self.message.get("peripherals", [])
        return []

    def to_task_register(self) -> List[str]:
        """Try to extract the task register message"""

        if self.message.get("type", "") == self.REGISTER_TYPE:
            return self.message.get("tasks", [])
        return []

    def to_telemetry(self):
        """"Try to extract telemetry"""

        if self.message.get("type", "") == self.TELEMETRY_TYPE:
            return self.message
        return {}

    def get_type(self):
        """Get the message type"""

        return self.message.get("type", "")

    @classmethod
    def to_command_message(
        cls,
        peripheral_commands: Optional[Dict] = None,
        task_commands: Optional[Dict] = None,
        request_id: Optional[str] = "",
    ) -> Dict:
        message = {"type": cls.COMMAND_TYPE}
        if peripheral_commands:
            message["peripheral"] = peripheral_commands
        if task_commands:
            message["task"] = task_commands
        if request_id:
            message["request_id"] = request_id
        return message
