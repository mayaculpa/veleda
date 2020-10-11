import uuid

from django.db import models

from farms.models.site import SiteEntity
from farms.models.controller import ControllerComponent

class PeripheralComponentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,)
    name = models.CharField(
        max_length=255, help_text="The name of this type, e.g., BME280 or LED."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return f"{self.name}"


class PeripheralComponent(models.Model):
    """The peripheral aspect of a site entity, such as a sensor or actuator."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,)
    component_type = models.ForeignKey(
        PeripheralComponentType,
        on_delete=models.CASCADE,
        help_text="The type of this peripheral component.",
    )
    site_entity = models.OneToOneField(
        SiteEntity,
        on_delete=models.CASCADE,
        help_text="Which site entity the component is a part of.",
    )
    controller_component = models.ForeignKey(
        ControllerComponent,
        on_delete=models.CASCADE,
        help_text="Which controller controls and is connected to this peripheral.",
    )
    config = models.JSONField(
        help_text="The config sent to the controller to perform setup excl. the name."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return f"Peripheral of {self.site_entity.name}"