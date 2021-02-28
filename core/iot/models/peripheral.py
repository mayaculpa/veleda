import uuid
from typing import Dict, List, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ValidationError
from django.db import models, transaction
from iot.models.controller import ControllerComponent
from iot.models.site import SiteEntity


class PeripheralDataPointType(models.Model):
    """Intermediate model linking data point types and peripherals. Contains the prefix
    needed for setting up peripherals regarding the data point type."""

    data_point_type = models.ForeignKey(
        "DataPointType",
        on_delete=models.PROTECT,
        related_name="peripheral_component_edges",
    )
    peripheral = models.ForeignKey(
        "PeripheralComponent",
        on_delete=models.CASCADE,
        related_name="data_point_type_edges",
    )
    parameter_prefix = models.CharField(blank=True, max_length=64)

    @property
    def parameter_name(self) -> str:
        """Get the name of the data point type parameter"""

        if self.parameter_prefix:
            key = f"{self.parameter_prefix}_data_point_type"
        else:
            key = "data_point_type"
        return key

    @property
    def parameter(self) -> Dict[str, uuid.UUID]:
        """Get data point type parameter in the form of
        {parameter_name: data_point_type_id}."""

        return {self.parameter_name: self.data_point_type_id}


class PeripheralComponentManager(models.Manager):
    def create_with_new_site_enitity_and_send(
        self,
        name: str,
        site_id: uuid.UUID,
        controller_component_id: uuid.UUID,
        peripheral_type: str,
        other_parameters: Dict,
        data_point_type_edges: Dict[uuid.UUID, str],
    ) -> "PeripheralComponent":
        """Create a peripheral component with a new site entity and send a request to the
        controller to add it."""

        with transaction.atomic():
            site_entity = SiteEntity.objects.create(name=name, site_id=site_id)
            peripheral_component = PeripheralComponent(
                site_entity_id=site_entity.pk,
                controller_component_id=controller_component_id,
                state=self.model.State.ADDING,
                peripheral_type=peripheral_type,
                other_parameters=other_parameters,
            )
            try:
                peripheral_component.full_clean()
            except ValidationError as err:
                raise ValueError from err
            peripheral_component.save()
            peripheral_data_point_types = []
            for data_point_type_id, parameter_prefix in data_point_type_edges.items():
                peripheral_data_point_types.append(
                    PeripheralDataPointType(
                        data_point_type_id=data_point_type_id,
                        peripheral_id=peripheral_component.pk,
                        parameter_prefix=parameter_prefix,
                    )
                )
            PeripheralDataPointType.objects.bulk_create(peripheral_data_point_types)
            # Refetch model due to added data point type edges
            peripheral_component = (
                PeripheralComponent.objects.prefetch_related("data_point_type_set")
                .select_related("controller_component")
                .get(pk=peripheral_component.pk)
            )
            commands = self.to_commands([peripheral_component])
            self._send_commands_to_controller(
                peripheral_component.controller_component.channel_name, commands
            )
        return peripheral_component

    def to_commands(self, peripherals: List["PeripheralComponent"]) -> Dict:
        """Convert a list of peripherals to commands. Ignores peripherals that cannot
        be converted to commands"""

        add_peripherals = []
        remove_peripherals = []
        for peripheral in peripherals:
            if peripheral.state == self.model.State.ADDING:
                add_peripherals.append(peripheral.to_add_command())
            if peripheral.state == self.model.State.REMOVING:
                remove_peripherals.append(peripheral.to_remove_command())

        commands = {}
        if add_peripherals:
            commands.update({"add": add_peripherals})
        if remove_peripherals:
            commands.update({"remove": remove_peripherals})
        return commands

    def from_results(self, results: Dict) -> List["PeripheralComponent"]:
        """Update states from results commands"""

        # Get all peripheral ids to update
        uuids = [result["uuid"] for result in results.get("add", [])]
        uuids.extend([result["uuid"] for result in results.get("remove", [])])
        peripherals = self.select_for_update().filter(pk__in=uuids)

        with transaction.atomic():
            for add_result in results.get("add", []):
                next(
                    peripheral
                    for peripheral in peripherals
                    if str(peripheral.pk) == add_result["uuid"]
                ).apply_add_result(add_result)
            for remove_result in results.get("remove", []):
                next(
                    peripheral
                    for peripheral in peripherals
                    if str(peripheral.pk) == remove_result["uuid"]
                ).apply_remove_result(remove_result)
            self.bulk_update(peripherals, ["state"])
        return peripherals

    def commands_from_register(
        self, added_peripherals: List[str], controller_id: uuid.UUID
    ) -> Dict:
        """Updates peripherals to be re-added to the adding state and returns commands
        to re-add peripherals to a controller. However, exclude those that the
        controller reports to have already been added. The commands are ordered from
        oldest to newest to preserve initialization order."""

        peripherals = (
            PeripheralComponent.objects.filter(controller_component__pk=controller_id)
            .filter(state__in=PeripheralComponent.RE_ADD_STATES)
            .exclude(pk__in=added_peripherals)
            .order_by("created_at")
            .select_for_update()
        )

        with transaction.atomic():
            for peripheral in peripherals:
                peripheral.state = PeripheralComponent.State.ADDING
            self.bulk_update(peripherals, ["state"])

        commands = []
        for peripheral in peripherals:
            commands.append(peripheral.to_add_command())
        if commands:
            return {"add": commands}
        return {}

    @staticmethod
    def _send_commands_to_controller(
        channel_name: str, peripheral_commands: List[Dict], request_id: str = None
    ) -> None:
        """Send peripheral commands to the controller"""

        if not channel_name:
            raise ValueError("Controller has not connected to the server")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(
            channel_name,
            {
                "type": "send.peripheral.commands",
                "commands": peripheral_commands,
                "request_id": request_id,
            },
        )


def validate_other_parameters(value):
    """Ensure that data point types are not included in other parameters"""

    for key in value.keys():
        if "data_point_type" in key:
            raise ValidationError(
                "Store data point type parameters through data point type edges",
                params={"value": value},
            )


class PeripheralComponent(models.Model):
    """The peripheral aspect of a site entity, such as a sensor or actuator."""

    objects = PeripheralComponentManager()

    class InvalidTransition(Exception):
        """Thrown when an invalid state change is applied"""

    class State(models.TextChoices):
        """Possible peripheral states."""

        ADDING = ("adding", "Adding")
        ADDED = ("added", "Added")
        FAILED = ("failed", "Failed")
        REMOVING = ("removing", "Removing")
        REMOVED = ("removed", "Removed")

    # States for which remove commands for peripherals can be created
    REMOVABLE_STATES = [State.ADDING.value, State.ADDED.value, State.REMOVING.value]
    # States to add peripherals again (registration after reboot)
    RE_ADD_STATES = [State.ADDING.value, State.ADDED.value]

    class PeripheralType(models.TextChoices):
        """Possible peripheral types."""

        INVALID_TYPE = ("InvalidPeripheral", "Invalid peripheral")
        DIGITAL_IN = ("DigitalIn", "Digital in")
        DIGITAL_OUT = ("DigitalOut", "Digital out")
        ANALOG_IN = ("AnalogIn", "Analog in")
        ANALOG_OUT = ("AnalogOut", "Analog out")
        PWM = ("PWM", "PWM")
        BME280_SENSOR = ("BME280", "BME/BMP 280 sensor")
        AS_EC_METER_I2C = ("AsEcMeterI2C", "Atlas Scientific EC Meter (I2C)")
        CAPACITIVE_SENSOR = ("CapacitiveSensor", "Capacitive sensor")
        I2C_ADAPTER = ("I2CAdapter", "I2C Adapter")
        NEO_PIXEL = ("NeoPixel", "NeoPixel array")

    site_entity = models.OneToOneField(
        SiteEntity,
        primary_key=True,
        related_name="peripheral_component",
        on_delete=models.CASCADE,
        help_text="Which site entity the component is a part of.",
    )
    controller_component = models.ForeignKey(
        ControllerComponent,
        on_delete=models.CASCADE,
        related_name="peripheral_component_set",
        help_text="Which controller controls and is connected to this peripheral.",
    )
    peripheral_type = models.CharField(
        default=PeripheralType.INVALID_TYPE.value,
        choices=PeripheralType.choices,
        max_length=64,
        help_text="The type of this peripheral component.",
    )
    state = models.CharField(
        choices=State.choices,
        max_length=64,
        help_text="The state of the controller task.",
    )
    other_parameters = models.JSONField(
        default=dict,
        help_text="Setup parameters excl. the data point type parameters.",
        validators=[validate_other_parameters],
        blank=True,
    )

    data_point_type_set = models.ManyToManyField(
        "DataPointType",
        through="PeripheralDataPointType",
        related_name="peripheral_component_set",
    )

    @property
    def parameters(self):
        """Get all peripheral setup parameters, combining the data point type ones with
        the others."""

        data_point_types = {
            parameter_name: str(dpt_id)
            for edge in self.data_point_type_edges.all()
            for parameter_name, dpt_id in edge.parameter.items()
        }
        return {**data_point_types, **self.other_parameters}

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def to_add_command(self) -> Optional[Dict]:
        """If in adding state, return a command that adds the peripheral, else None"""

        if self.state == self.State.ADDING:
            return {
                "uuid": str(self.pk),
                "type": self.peripheral_type,
                **self.parameters,
            }
        return None

    def to_remove_command(self) -> Optional[Dict]:
        """If in removing state, return a command that removes the peripheral, else None"""

        if self.state == self.State.REMOVING:
            return {"uuid": str(self.pk)}
        return None

    def apply_add_result(self, result):
        """Modify the state accoring to the result"""

        status = result["status"]
        if self.state == self.State.ADDING and status == "success":
            self.state = self.State.ADDED
        elif self.state == self.State.ADDING and status == "fail":
            self.state = self.State.FAILED
        else:
            raise self.InvalidTransition(
                f"Apply add result {status} to {self.state}", id=self.pk
            )

    def apply_remove_result(self, result):
        """Modify the state with a remove result"""

        status = result["status"]
        if self.state == self.State.REMOVING and status == "success":
            self.state = self.State.REMOVED
        elif self.state == self.State.REMOVING and status == "fail":
            self.state = self.State.ADDED
        else:
            raise self.InvalidTransition(
                f"Apply remove result {status} to {self.state}", id=self.pk
            )

    def __str__(self):
        if self.site_entity.name:
            return f"Peripheral of {self.site_entity.name}"
        return f"Peripheral of {self.peripheral_type} - {str(self.pk)[:5]}"
