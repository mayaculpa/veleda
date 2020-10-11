import uuid

from django.db import models, IntegrityError
from accounts.models import User
from macaddress.fields import MACAddressField

from farms.models.site import Site


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
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The site to which the coordinator belongs.",
    )
    local_ip_address = models.GenericIPAddressField(
        help_text="The coordinator's local IP address."
    )
    external_ip_address = models.GenericIPAddressField(
        help_text="The coordinator's external IP address."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the coordinator was first registered.",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the coordinator was last updated.",
    )
    channel_name = models.CharField(
        null=False,
        default="",
        max_length=64,
        help_text="The channel name of the connected WebSocket.",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The user account with which the coordinator can log in.",
    )

    def get_email_address(self):
        """Returns an email address based on a coordinator's ID"""
        return f"{self.id}@coordinator.localhost"

    def create_user_account(self, password, save=True):
        """Creates a user account for this coordinator"""
        self.user = User.objects.create_user(self.get_email_address(), password)
        if save:
            self.save()

    def __str__(self):
        if self.site:
            return self.site.name + " Coordirnator"
        return str(self.id)


class HydroponicSystem(models.Model):
    """A system in which plants can be grown. It is associated with multiple hydroponic
    components."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The UUID to identify the hydroponic system.",
    )

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

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
        return self.get_system_type_display() + " (" + str(self.id) + ")"


class ControllerManager(models.Manager):
    def get_local_unregistered(self, external_ip_address):
        """Finds all unregistered controllers in the same local network (sharing an
           external IP address)"""

        queryset = self.get_queryset()
        return queryset.filter(external_ip_address=external_ip_address).filter(
            coordinator__isnull=True
        )


class Controller(models.Model):
    """A component of the hydroponic system that can be commanded (e.g., pump, dosage, camera or
    sensor controller)"""

    objects = ControllerManager()

    PUMP_TYPE = "PUM"
    DOSAGE_TYPE = "DOS"
    CAMERA_TYPE = "CAM"
    SENSOR_TYPE = "SEN"
    UNKNOWN_TYPE = "UNK"

    CONTROLLER_TYPE_CHOICES = [
        (PUMP_TYPE, "Pump controller"),
        (DOSAGE_TYPE, "Dosage controller"),
        (CAMERA_TYPE, "Camera controller"),
        (SENSOR_TYPE, "Sensor controller"),
        (UNKNOWN_TYPE, "Unknown controller"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The UUID to identify the controller.",
    )
    name = models.CharField(
        max_length=30, null=True, blank=True, help_text="The name of the controller",
    )
    coordinator = models.ForeignKey(
        Coordinator,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The coordinator with which the controller is connected to.",
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        help_text="The site to which the controller is assigned to.",
    )
    wifi_mac_address = MACAddressField(
        help_text="The Wifi MAC address of the controller."
    )
    external_ip_address = models.GenericIPAddressField(
        help_text="The external IP address of the controller."
    )
    controller_type = models.CharField(
        max_length=3,
        choices=CONTROLLER_TYPE_CHOICES,
        default=UNKNOWN_TYPE,
        help_text="The main function of the controller (e.g., pump or sensor controller).",
    )
    channel_name = models.CharField(
        null=False,
        blank=True,
        default="",
        max_length=128,
        help_text="The channel name of the connected WebSocket.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the controller was first registered.",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the controller was last updated.",
    )

    def __str__(self):
        if self.name:
            return self.get_controller_type_display() + " (" + self.name + ")"
        return self.get_controller_type_display() + " (" + str(self.id) + ")"


class MqttMessage(models.Model):
    """An MQTT message from a coordinator's MQTT broker"""

    class Meta:
        unique_together = ["created_at", "coordinator"]

    COMMAND_PREFIX = "cmd"
    TELEMETRY_PREFIX = "tel"
    REGISTER_PREFIX = "reg"

    TOPIC_PREFIX_CHOICES = [
        (COMMAND_PREFIX, "Command topic"),
        (TELEMETRY_PREFIX, "Telemetry topic"),
        (REGISTER_PREFIX, "Register topic"),
    ]

    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime when the message was received",
    )
    coordinator = models.ForeignKey(
        Coordinator,
        on_delete=models.CASCADE,
        help_text="The coordinator that relayed the message.",
    )
    message = models.JSONField()
    controller = models.ForeignKey(
        Controller,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If not None, the sender of the message.",
    )
    topic_prefix = models.CharField(
        max_length=3,
        choices=TOPIC_PREFIX_CHOICES,
        help_text="The purpose of the message.",
    )
    topic_suffix = models.CharField(
        max_length=30, default="", help_text="The context of the message."
    )