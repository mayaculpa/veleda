from django.db import models

from iot.models.site import SiteEntity
from iot.models.peripheral import PeripheralComponent


class HydroponicSystemPeripheral(models.Model):
    """Intermediate model linking peripherals and hydroponic systems."""

    peripheral = models.ForeignKey(
        PeripheralComponent,
        on_delete=models.CASCADE,
        related_name="hydroponic_system_component_edges",
    )
    hydroponic_system = models.ForeignKey(
        "HydroponicSystemComponent",
        on_delete=models.CASCADE,
        related_name="peripheral_component_edges",
    )


class HydroponicSystemComponent(models.Model):
    """The hydroponic system component of a site entity, such as a NFT,
    vertical or flood and drain system"""

    class HydroponicSystemType(models.TextChoices):
        """Possible hydroponic system types"""

        NFT = ("NFT", "NFT System",)
        FLOOD_DRAIN = ("FloodDrain", "Flood & Drain System")
        VERTICAL = ("Vertical", "Vertical System")
        DWC = ("DWC", "DWC System")

    site_entity = models.OneToOneField(
        SiteEntity,
        primary_key=True,
        related_name="hydroponic_system_component",
        on_delete=models.CASCADE,
        help_text="Which site entity the component is a part of.",
    )
    hydroponic_system_type = models.CharField(
        choices=HydroponicSystemType.choices,
        max_length=64,
        help_text="The type of hydroponic system",
    )
    peripheral_component_set = models.ManyToManyField(
        PeripheralComponent,
        through="HydroponicSystemPeripheral",
        related_name="hydroponic_system_component_set",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return f"{self.hydroponic_system_type}: {self.site_entity.name}"
