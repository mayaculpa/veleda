import uuid

from django.test import TestCase

from farms.models import (
    PeripheralComponent,
    ControllerComponent,
    ControllerComponentType,
    SiteEntity,
    Site,
)
from django.contrib.auth import get_user_model


class PeripheralModelTests(TestCase):
    """Test the peripheral model"""

    def setUp(self):
        self.site_a = Site.objects.create(
            name="Site A",
            owner=get_user_model().objects.create_user(
                email="owner@bar.com",
                password="foo",
            ),
        )
        self.esp32_a_entity = SiteEntity.objects.create(
            name="ESP32 A", site=self.site_a
        )
        self.esp32_type = ControllerComponentType.objects.create(name="ESP32")
        self.esp32_a_controller = ControllerComponent.objects.create(
            id=uuid.uuid4(),
            component_type=self.esp32_type,
            site_entity=self.esp32_a_entity,
        )
        self.add_commands = [
            {
                "uuid": str(uuid.uuid4()),
                "type": PeripheralComponent.LED_TYPE,
                "name": "LED A",
                "pin": 12,
                "data_point_type": str(uuid.uuid4()),
            },
            {
                "uuid": str(uuid.uuid4()),
                "type": PeripheralComponent.I2C_ADAPTER_TYPE,
                "name": "I2C Adapter A",
                "scl": 32,
                "sda": 33,
            },
        ]
        self.remove_commands = [
            {"uuid": self.add_commands[0]["uuid"]},
            {"uuid": self.add_commands[1]["uuid"]},
        ]

    def test_creation(self):
        """Test creating peripherals"""

        led_a_entity = SiteEntity.objects.create(name="LED A", site=self.site_a)
        led_a_peripheral = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.LED_TYPE,
            site_entity=led_a_entity,
            controller_component=self.esp32_a_controller,
            state=PeripheralComponent.ADDING_STATE,
        )
        self.assertEqual(led_a_peripheral.site_entity, led_a_entity)
        self.assertEqual(led_a_peripheral.controller_component, self.esp32_a_controller)
        self.assertEqual(led_a_peripheral.site_entity.site, self.site_a)

    def test_from_add_commands(self):
        """Test parsing add command message"""

        add_peripherals = PeripheralComponent.objects.from_add_commands(
            self.add_commands, self.esp32_a_controller
        )

        # Check that multiple objects are parsed
        peripheral_0 = next(
            i for i in add_peripherals if i.id == self.add_commands[0]["uuid"]
        )
        peripheral_1 = next(
            i for i in add_peripherals if i.id == self.add_commands[1]["uuid"]
        )
        self.assertIn(peripheral_0.id, self.add_commands[0]["uuid"])
        self.assertIn(peripheral_1.id, self.add_commands[1]["uuid"])

        # Check correct parsing of other peripheral properties
        self.assertEqual(peripheral_0.peripheral_type, self.add_commands[0]["type"])
        self.assertEqual(peripheral_0.site_entity.name, self.add_commands[0]["name"])
        self.assertEqual(peripheral_0.parameters["pin"], self.add_commands[0]["pin"])

        self.assertEqual(peripheral_1.peripheral_type, self.add_commands[1]["type"])
        self.assertEqual(peripheral_1.site_entity.name, self.add_commands[1]["name"])
        self.assertEqual(peripheral_1.parameters["scl"], self.add_commands[1]["scl"])

        # Check that both peripherals were created
        uuids = [add_command["uuid"] for add_command in self.add_commands]
        queried_peripherals = list(PeripheralComponent.objects.filter(id__in=uuids))
        self.assertNotEqual(queried_peripherals[0].id, queried_peripherals[1].id)
        self.assertIn(str(queried_peripherals[0].id), uuids)
        self.assertIn(str(queried_peripherals[1].id), uuids)

    def test_from_remove_commands(self):
        """Test parsing remove command message"""

        # Check that no peripherals are returned if the uuids don't match
        remove_peripherals = PeripheralComponent.objects.from_remove_commands(
            self.remove_commands
        )
        self.assertFalse(remove_peripherals)

        # Check that the state has to be removable (created peripherals are "adding")
        add_peripherals = PeripheralComponent.objects.from_add_commands(
            self.add_commands, self.esp32_a_controller
        )
        failed_peripheral = add_peripherals.pop()
        failed_peripheral.state = PeripheralComponent.FAILED_STATE
        failed_peripheral.save()
        self.assertNotIn(
            PeripheralComponent.FAILED_STATE, PeripheralComponent.REMOVABLE_STATES
        )
        self.assertNotIn(
            PeripheralComponent.REMOVED_STATE, PeripheralComponent.REMOVABLE_STATES
        )
        remove_peripherals = PeripheralComponent.objects.from_remove_commands(
            self.remove_commands
        )
        remove_uuids = [
            remove_peripheral.id for remove_peripheral in remove_peripherals
        ]
        self.assertNotEqual(failed_peripheral.id, remove_uuids)
        self.assertIn(remove_peripherals[0].id, remove_uuids)

    def test_from_commands_message(self):
        """Test parsing """
