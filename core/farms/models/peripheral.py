from typing import Dict, List, Type, Optional
import uuid

from django.db import models, IntegrityError, transaction

from farms.models.site import SiteEntity
from farms.models.controller import ControllerComponent


class PeripheralComponentManager(models.Manager):
    def from_commands(
        self, peripheral_commands: Dict, controller: Type[ControllerComponent]
    ) -> List[Type["PeripheralComponent"]]:
        """Create peripherals from add commands and get peripherals to be removed.
        Throws ValueError on missing keys."""

        peripherals: List[Type["PeripheralComponent"]] = []
        if peripheral_commands:
            add_commands = peripheral_commands.get("add")
            if add_commands:
                peripherals.extend(self.from_add_commands(add_commands, controller))
            remove_commands = peripheral_commands.get("remove")
            if remove_commands:
                peripherals.extend(self.from_remove_commands(remove_commands))
        return peripherals

    def from_add_commands(
        self,
        add_commands: Dict,
        controller: Type[ControllerComponent],
    ) -> List[Type["PeripheralComponent"]]:
        """Create peripherals from add commands. Throws ValueError on missing keys."""

        peripherals: List[Type["PeripheralComponent"]] = []
        site = controller.site_entity.site
        for add_command in add_commands:
            command = add_command.copy()
            try:
                peripheral_id = command.pop("uuid")
                peripheral_type = command.pop("type")
                name = command.pop("name")
            except KeyError as err:
                if "peripheral_id" in locals():
                    raise ValueError(f"Missing key {err} for {peripheral_id}") from err
                raise ValueError(f"Missing key {err}") from err
            peripherals.append(
                self.model(
                    id=peripheral_id,
                    site_entity=SiteEntity.objects.create(site=site, name=name),
                    controller_component=controller,
                    peripheral_type=peripheral_type,
                    state=self.model.ADDING_STATE,
                    parameters=command,
                )
            )
        try:
            return self.bulk_create(peripherals)
        except IntegrityError as err:
            raise ValueError(f"Duplicate UUID") from err

    def from_remove_commands(
        self, remove_commands: Dict
    ) -> List[Type["PeripheralComponent"]]:
        """Get the list of peripherals to be removed. Throws ValueError on missing keys."""

        try:
            uuids = [command["uuid"] for command in remove_commands]
        except KeyError as err:
            raise ValueError(f"Missing key {err}") from err
        peripherals = list(
            self.filter(id__in=uuids).filter(state__in=self.model.REMOVABLE_STATES)
        )
        for peripheral in peripherals:
            peripheral.state = self.model.REMOVING_STATE
        self.bulk_update(peripherals, ["state"])
        return peripherals

    def from_results(self, results: Dict) -> List[Type["PeripheralComponent"]]:
        """Update states from results commands"""

        # Get all peripheral ids to update
        uuids = [result["uuid"] for result in results.get("add", [])]
        uuids.extend([result["uuid"] for result in results.get("remove", [])])
        peripherals = self.select_for_update().filter(id__in=uuids)

        with transaction.atomic():
            for add_result in results.get("add", []):
                next(
                    peripheral
                    for peripheral in peripherals
                    if str(peripheral.id) == add_result["uuid"]
                ).apply_add_result(add_result)
            for remove_result in results.get("remove", []):
                next(
                    peripheral
                    for peripheral in peripherals
                    if str(peripheral.id) == remove_result["uuid"]
                ).apply_remove_result(remove_result)
            self.bulk_update(peripherals, ["state"])
        return peripherals


class PeripheralComponent(models.Model):
    """The peripheral aspect of a site entity, such as a sensor or actuator."""

    objects = PeripheralComponentManager()

    class InvalidTransition(Exception):
        """Thrown when an invalid state change is applied"""

    ADDING_STATE = "adding"
    ADDED_STATE = "added"
    FAILED_STATE = "failed"
    REMOVING_STATE = "removing"
    REMOVED_STATE = "removed"

    REMOVABLE_STATES = [ADDING_STATE, ADDED_STATE, REMOVING_STATE]

    STATE_CHOICES = [
        (ADDING_STATE, "Adding"),
        (ADDED_STATE, "Added"),
        (FAILED_STATE, "Failed"),
        (REMOVING_STATE, "Removing"),
        (REMOVED_STATE, "Removed"),
    ]

    INVALID_TYPE = "InvalidPeripheral"
    BME280_TYPE = "BME280"
    CAPACITIVE_SENSOR_TYPE = "CapacitiveSensor"
    I2C_ADAPTER_TYPE = "I2CAdapter"
    LED_TYPE = "LED"
    NEO_PIXEL_TYPE = "NeoPixel"

    TYPE_CHOICES = [
        (INVALID_TYPE, "Invalid peripheral"),
        (BME280_TYPE, "BME/BMP 280 sensor"),
        (CAPACITIVE_SENSOR_TYPE, "Capacitive sensor"),
        (I2C_ADAPTER_TYPE, "I2C Adapter"),
        (LED_TYPE, "LED"),
        (NEO_PIXEL_TYPE, "NeoPixel array"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
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
    peripheral_type = models.CharField(
        default=INVALID_TYPE,
        choices=TYPE_CHOICES,
        max_length=64,
        help_text="The type of this peripheral component.",
    )
    state = models.CharField(
        choices=STATE_CHOICES,
        max_length=64,
        help_text="The state of the controller task.",
    )
    parameters = models.JSONField(
        default=list, help_text="Parameters for setup on controller excl. type"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    @classmethod
    def to_commands(cls, peripherals: List[Type["PeripheralComponent"]]) -> Dict:
        """Convert a list of peripherals to commands. Ignores peripherals that cannot
        be converted to commands"""

        add_peripherals = []
        remove_peripherals = []
        for peripheral in peripherals:
            if peripheral.state == cls.ADDING_STATE:
                add_peripherals.append(peripheral.to_add_command())
            if peripheral.state == cls.REMOVING_STATE:
                remove_peripherals.append(peripheral.to_remove_command())

        commands = {}
        if add_peripherals:
            commands.update({"add": add_peripherals})
        if remove_peripherals:
            commands.update({"remove": remove_peripherals})
        return commands

    def to_add_command(self) -> Optional[Dict]:
        """If in adding state, return a command that adds the peripheral, else None"""

        if self.state == self.ADDING_STATE:
            return {
                "uuid": str(self.id),
                "type": self.peripheral_type,
                **self.parameters,
            }
        return None

    def to_remove_command(self) -> Optional[Dict]:
        """If in removing state, return a command that removes the peripheral, else None"""

        if self.state == self.REMOVING_STATE:
            return {"uuid": str(self.id)}
        return None

    def apply_add_result(self, result):
        """Modify the state accoring to the result"""

        status = result["status"]
        if self.state == self.ADDING_STATE and status == "success":
            self.state = self.ADDED_STATE
        elif self.state == self.ADDING_STATE and status == "fail":
            self.state = self.FAILED_STATE
        else:
            raise self.InvalidTransition(
                f"Apply add result {status} to {self.state}", id=self.id
            )

    def apply_remove_result(self, result):
        """Modify the state with a remove result"""

        status = result["status"]
        if self.state == self.REMOVING_STATE and status == "success":
            self.state = self.REMOVED_STATE
        elif self.state == self.REMOVING_STATE and status == "fail":
            self.state = self.ADDED_STATE
        else:
            raise self.InvalidTransition(
                f"Apply remove result {status} to {self.state}", id=self.id
            )

    def __str__(self):
        if self.site_entity.name:
            return f"Peripheral of {self.site_entity.name}"
        return f"Peripheral of {self.peripheral_type} - {str(self.id)[:5]}"
