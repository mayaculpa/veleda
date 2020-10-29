import binascii
import os
import uuid
from typing import Dict, Optional

from django.conf import settings
from django.db import models

from farms.models.site import SiteEntity


class ControllerComponentType(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=255, help_text="The name of this type, e.g., ESP32 or RasberryPi4"
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component_type = models.ForeignKey(
        ControllerComponentType,
        on_delete=models.CASCADE,
        help_text="The type of which this component is an instance of.",
    )
    site_entity = models.OneToOneField(
        SiteEntity,
        related_name="controller_component",
        on_delete=models.CASCADE,
        help_text="Which site entity the component is a part of.",
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


class ControllerAuthToken(models.Model):
    """Token for controller models."""

    key = models.CharField(max_length=128, primary_key=True)
    controller = models.OneToOneField(
        ControllerComponent, related_name="auth_token", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """Saves the controller token and generates a key if it has not been set"""
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        """Generates a random token based with a length of CONTROLLER_TOKEN_BYTES """
        return binascii.hexlify(os.urandom(settings.CONTROLLER_TOKEN_BYTES)).decode()

    def __str__(self):
        return self.key


class ControllerMessage(models.Model):
    """A message to/from a controller"""

    class Meta:
        unique_together = ["created_at", "controller"]

    COMMAND_TYPE = "cmd"
    TELEMETRY_TYPE = "tel"
    REGISTER_TYPE = "reg"
    ERROR_TYPE = "err"
    RESULT_TYPE = "result"

    TYPES = [
        COMMAND_TYPE,
        TELEMETRY_TYPE,
        REGISTER_TYPE,
        ERROR_TYPE,
        RESULT_TYPE,
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
        help_text="The ID of the request, to enable tracking requests",
    )

    def to_task_commands(self) -> Dict:
        """Try to extract the task commands"""

        return self.message.get("task", {})

    def to_peripheral_commands(self) -> Dict:
        """Try to extract the peripheral commands"""

        return self.message.get("peripheral", {})

    @classmethod
    def to_command_message(
        cls,
        peripheral_commands: Optional[Dict] = None,
        task_commands: Optional[Dict] = None,
        request_id="",
    ) -> Dict:
        message = {"type": cls.COMMAND_TYPE}
        if peripheral_commands:
            message["peripheral"] = peripheral_commands
        if task_commands:
            message["task"] = task_commands
        if request_id:
            message["request_id"] = request_id
        return message
