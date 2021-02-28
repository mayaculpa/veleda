from greenhouse.models.hydroponic_system import HydroponicSystemComponent
from typing import List, Tuple
import uuid
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from iot.models.site import SiteEntity


class WaterCycle(models.Model):
    """A closed loop of water, isolated from other loops."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, help_text="The name of the water cycle")

    def __str__(self):
        return f"Water cycle: {self.name}"


class WaterCycleLog(models.Model):
    """A log of when a water cycle component was assigned to a water cycle"""

    water_cycle_component = models.ForeignKey(
        "WaterCycleComponent",
        on_delete=models.CASCADE,
        related_name="water_cycle_log_edges",
    )
    water_cycle = models.ForeignKey(
        WaterCycle,
        on_delete=models.CASCADE,
        related_name="water_cycle_component_log_edges",
    )
    since = models.DateTimeField(
        default=datetime.now,
        help_text="The time from when a water cycle component was part of a water cycle.",
    )
    until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The time until when a water cycle component was part of a water cycle.",
    )


class WaterCycleFlowsTo(models.Model):
    """Intermediate model linking water cycles."""

    flows_from = models.ForeignKey(
        "WaterCycleComponent",
        on_delete=models.CASCADE,
        related_name="flows_to_edges",
    )
    flows_to = models.ForeignKey(
        "WaterCycleComponent",
        on_delete=models.CASCADE,
        related_name="flows_from_edges",
    )


class WaterCycleComponentManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "water_cycle",
                "site_entity__hydroponic_system_component",
                "water_reservoir",
                "water_pipe",
                "water_pump",
                "water_sensor",
                "water_valve",
            )
        )


def is_type(func):
    """Wrapper to handle existance check of OneToOneFields"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ObjectDoesNotExist:
            return False

    return wrapper


class WaterCycleComponentType(models.TextChoices):
    """Possible water sensor types."""

    HYDROPONIC_SYSTEM = ("HydroponicSystem", "Hydroponic system")
    WATER_RESERVOIR = ("WaterReservoir", "Water reservoir")
    WATER_PIPE = ("WaterPipe", "Water pipe")
    WATER_PUMP = ("WaterPump", "Water pump")
    WATER_SENSOR = ("WaterSensor", "Water sensor")
    WATER_VALVE = ("WaterValve", "Water valve")


class WaterCycleComponent(models.Model):
    """The water cycle aspect of a site entity."""

    site_entity = models.OneToOneField(
        SiteEntity,
        primary_key=True,
        related_name="water_cycle_component",
        on_delete=models.CASCADE,
        help_text="Which site entity the component is a part of.",
    )
    water_cycle = models.ForeignKey(
        WaterCycle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="water_cycle_component",
        help_text="To which water cycle this site entity belongs to.",
    )
    water_cycle_log_set = models.ManyToManyField(
        WaterCycle,
        through=WaterCycleLog,
        related_name="water_cycle_component_log_set",
        help_text="A log of when this water cycle component was connected to which water cycle.",
    )
    flows_to_set = models.ManyToManyField(
        "self",
        through="WaterCycleFlowsTo",
        related_name="flows_from_set",
        symmetrical=False,
        help_text="The set of water cycle components to which water flows.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    objects = WaterCycleComponentManager()

    @is_type
    def is_hydroponic_system(self):
        """Checks if this is a hydroponic system."""
        return bool(self.site_entity.hydroponic_system_component)

    @is_type
    def is_water_reservoir(self):
        """Checks if this is a water reservoir."""
        return bool(self.water_reservoir)

    @is_type
    def is_water_pipe(self):
        """Checks if this is a water pipe."""
        return bool(self.water_pipe)

    @is_type
    def is_water_pump(self):
        """Checks if this is a water pump."""
        return bool(self.water_pump)

    @is_type
    def is_water_sensor(self):
        """Checks if this is a water sensor."""
        return bool(self.water_sensor)

    @is_type
    def is_water_valve(self):
        """Checks if this is a water valve."""
        return bool(self.water_valve)

    def get_types(self) -> List[Tuple]:
        """Returns the aspects of the water cycle component."""
        types = []
        if self.is_hydroponic_system():
            types.append(WaterCycleComponentType.HYDROPONIC_SYSTEM)
        if self.is_water_reservoir():
            types.append(WaterCycleComponentType.WATER_RESERVOIR)
        if self.is_water_pipe():
            types.append(WaterCycleComponentType.WATER_PIPE)
        if self.is_water_pump():
            types.append(WaterCycleComponentType.WATER_PUMP)
        if self.is_water_sensor():
            types.append(WaterCycleComponentType.WATER_SENSOR)
        if self.is_water_valve():
            types.append(WaterCycleComponentType.WATER_VALVE)
        return types

    def get_type_values(self) -> List[str]:
        return [wcc_type.value for wcc_type in self.get_types()]

    def get_type_labels(self) -> List[str]:
        return [wcc_type.label for wcc_type in self.get_types()]

    def __str__(self):
        return f"Water cycle: {self.site_entity.name}"


class WaterReservoir(models.Model):
    """Aspects that define a water reservoir."""

    water_cycle_component = models.OneToOneField(
        WaterCycleComponent,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="water_reservoir",
        help_text="To which water cycle component it belongs.",
    )
    max_capacity = models.FloatField(help_text="The max capacity in liters.")
    max_water_level = models.FloatField(help_text="The max water level in meters.")


class WaterPump(models.Model):
    """Aspects that define a water pump."""

    water_cycle_component = models.OneToOneField(
        WaterCycleComponent,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="water_pump",
        help_text="To which water cycle component it belongs.",
    )

    def turn_on(self):
        """Uses controller tasks to turn the associated peripheral on."""
        raise NotImplementedError

    def turn_off(self):
        """Uses controller tasks to turn the associated peripheral off."""
        raise NotImplementedError

    def set_power(self, percentage):
        """Sets the pump to the percentage (0-1) via the associated peripheral"""
        raise NotImplementedError


class WaterPipe(models.Model):
    """Aspects that define a water pipe."""

    water_cycle_component = models.OneToOneField(
        WaterCycleComponent,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="water_pipe",
        help_text="To which water cycle component it belongs.",
    )
    length = models.FloatField(help_text="The length of the pipe in meters.")


class WaterSensor(models.Model):
    """Aspects that define a water sensor."""

    class SensorType(models.TextChoices):
        """Possible water sensor types."""

        INVALID_TYPE = ("InvalidSensor", "Invalid sensor")
        TEMPERATURE = ("Temperature", "Temperature sensor")
        PH_METER = ("PhMeter", "pH meter")
        EC_METER = ("EcMeter", "EC meter")
        TDS_METER = ("TdsMeter", "TDS meter")
        TURBIDITY_METER = ("TurbidityMeter", "Turbidity meter")

    water_cycle_component = models.OneToOneField(
        WaterCycleComponent,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="water_sensor",
        help_text="To which water cycle component it belongs.",
    )
    sensor_type = models.CharField(
        choices=SensorType.choices,
        max_length=64,
        help_text="The sensor type.",
    )

    def request_reading(self):
        """Start a controller task to get a single reading."""
        raise NotImplementedError

    def start_polling_for(self, interval: timedelta, duration: timedelta):
        """Poll a sensor every interval (excl. setup time) for a period of time."""
        raise NotImplementedError

    def start_polling_until(self, interval: timedelta, until: datetime):
        """Poll a sensor every interval (excl. setup time) until a point in time."""
        raise NotImplementedError


class WaterValve(models.Model):
    """Aspects that define a water valve."""

    water_cycle_component = models.OneToOneField(
        WaterCycleComponent,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="water_valve",
        help_text="To which water cycle component it belongs.",
    )

    def open_valve(self):
        """Uses controller tasks to open a valve."""
        raise NotImplementedError

    def close_valve(self):
        """Uses controller tasks to close a valve."""
        raise NotImplementedError
