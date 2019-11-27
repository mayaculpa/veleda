import uuid
from django.db import models
from django.db.models.query import QuerySet
from address.models import AddressField
from macaddress.fields import MACAddressField

from accounts.models import User

# Create your models here.
class Farm(models.Model):
    """A farm where plants are grown hydroponically. Contains all hydroponic systems
       and plants that are controlled by an on-site coordinator"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The UUID to identify the hydroponic system.",
    )
    name = models.CharField(max_length=30, help_text="The name of the farm.")
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The user that owns the farm.",
    )
    address = AddressField(
        on_delete=models.SET_NULL,
        null=True,
        help_text="The postal address and the coordinates of the farm",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the farm was first created.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The date and time when the farm was last updated."
    )

    def __str__(self):
        return self.name


class Coordinator(models.Model):
    """The coordinator instructs the the controllers on which tasks to perform and
       collects their data. During controller discovery (initial registration), the
       external IP addresses of the coordinator and controller are used."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The UUID to identify the hydroponic system.",
    )
    farm = models.OneToOneField(
        Farm,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The farm to which the coordinator belongs.",
    )
    local_ip_address = models.GenericIPAddressField(
        help_text="The coordinator's local IP address."
    )
    external_ip_address = models.GenericIPAddressField(
        help_text="The coordinator's external IP address."
    )
    dns_address = models.URLField(
        null=True,
        blank=True,
        help_text="The URL which can be used to find the local IP address.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the coordinator was first registered.",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the coordinator was last updated.",
    )

    def __str__(self):
        if self.farm:
            return self.farm.name + " Coordirnator"
        else:
            return self.id.hex


class HydroponicSystem(models.Model):
    """A system in which plants can be grown. It is associated with multiple hydroponic
    components."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The UUID to identify the hydroponic system.",
    )

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="The name of the hydroponic system",
    )

    VERTICAL_TOWER = "VT"
    FLOOD_AND_DRAIN = "FD"
    NUTRIENT_FILM_TECHNIQUE = "NFT"
    DEEP_WATER_CULTURE = "DWC"

    SYSTEM_TYPE_CHOICES = [
        (VERTICAL_TOWER, "Vertical tower"),
        (FLOOD_AND_DRAIN, "Flood and drain"),
        (NUTRIENT_FILM_TECHNIQUE, "Nutrient film technique"),
        (DEEP_WATER_CULTURE, "Deep water culture"),
    ]

    system_type = models.CharField(
        max_length=3,
        choices=SYSTEM_TYPE_CHOICES,
        default=VERTICAL_TOWER,
        help_text="The hydroponic system's type (e.g., vertical tower, flood and drain).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the hydroponic system was first registered.",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the hydroponic system was last updated.",
    )

    def __str__(self):
        if self.name:
            return self.get_system_type_display() + " (" + self.name + ")"
        else:
            return self.get_system_type_display() + " (" + self.id.hex + ")"


class ControllerQuerySet(QuerySet):
    def get_local_unregistered_controllers(self, external_ip_address):
        """Finds all unregistered controllers in the same local network (sharing an
           external IP address)"""

        return self.filter(external_ip_address=external_ip_address).filter(
            farm__isnull=True
        )


class Controller(models.Model):
    """A component of the hydroponic system that can be commanded (e.g., pump, dosage, camera or
    sensor controller)"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The UUID to identify the controller.",
    )
    name = models.CharField(
        max_length=30, null=True, blank=True, help_text="The name of the controller",
    )
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The farm to which the controller belongs to, and thus the coordinator.",
    )
    wifi_mac_address = MACAddressField(
        help_text="The Wifi MAC address of the controller."
    )
    external_ip_address = models.GenericIPAddressField(
        null=True, blank=True, help_text="The external IP address of the controller."
    )

    PUMP_CONTROLLER = "PC"
    DOSAGE_CONTROLLER = "DC"
    CAMERA_CONTROLLER = "CC"
    SENSOR_CONTROLLER = "SC"

    CONTROLLER_TYPE_CHOICES = [
        (PUMP_CONTROLLER, "Pump controller"),
        (DOSAGE_CONTROLLER, "Dosage controller"),
        (CAMERA_CONTROLLER, "Camera controller"),
        (SENSOR_CONTROLLER, "Sensor controller"),
    ]

    controller_type = models.CharField(
        max_length=3,
        choices=CONTROLLER_TYPE_CHOICES,
        default=PUMP_CONTROLLER,
        help_text="The main function of the controller (e.g., pump or sensor controller).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the controller was first registered.",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the controller was last updated.",
    )

    objects = ControllerQuerySet.as_manager()

    def __str__(self):
        if self.name:
            return self.get_controller_type_display() + " (" + self.name + ")"
        else:
            return self.get_controller_type_display() + " (" + self.id.hex + ")"
