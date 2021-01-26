from django.contrib.auth import get_user_model
from django.test import TestCase

from farms.models import (
    DataPointType,
    PeripheralDataPointType,
    PeripheralComponent,
    ControllerComponent,
    ControllerComponentType,
    SiteEntity,
    Site,
)


class PeripheralModelAddRemoveTests(TestCase):
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
            component_type=self.esp32_type,
            site_entity=self.esp32_a_entity,
        )

    def test_creation(self):
        """Test creating peripherals"""

        led_a_entity = SiteEntity.objects.create(name="LED A", site=self.site_a)
        led_a_peripheral = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.PWM,
            site_entity=led_a_entity,
            controller_component=self.esp32_a_controller,
            state=PeripheralComponent.State.ADDING,
            other_parameters={"some": "value"},
        )
        self.assertEqual(led_a_peripheral.site_entity, led_a_entity)
        self.assertEqual(led_a_peripheral.controller_component, self.esp32_a_controller)
        self.assertEqual(led_a_peripheral.site_entity.site, self.site_a)
        self.assertEqual(led_a_peripheral.pk, led_a_entity.pk)
        self.assertDictEqual(
            led_a_peripheral.other_parameters, led_a_peripheral.parameters
        )
        self.assertEqual(led_a_peripheral.state, PeripheralComponent.State.ADDING)
        self.assertEqual(
            led_a_peripheral.peripheral_type, PeripheralComponent.PeripheralType.PWM
        )

    def test_peripheral_data_point_type(self):
        bme280_entity = SiteEntity.objects.create(name="BME280", site=self.site_a)
        bme280_peripheral = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.BME280_SENSOR,
            site_entity=bme280_entity,
            controller_component=self.esp32_a_controller,
            state=PeripheralComponent.State.ADDING,
            other_parameters={"some": "value"},
        )
        temperature_data_point_type = DataPointType.objects.create(
            name="Temperature", unit="°C"
        )
        temperature_link = PeripheralDataPointType.objects.create(
            data_point_type=temperature_data_point_type,
            peripheral=bme280_peripheral,
            parameter_prefix="temperature",
        )
        pressure_data_point_type = DataPointType.objects.create(
            name="Pressure", unit="Pa"
        )
        pressure_link = PeripheralDataPointType.objects.create(
            data_point_type=pressure_data_point_type,
            peripheral=bme280_peripheral,
            parameter_prefix="pressure",
        )
        humidity_data_point_type = DataPointType.objects.create(
            name="Pressure", unit="Pa"
        )
        PeripheralDataPointType.objects.create(
            data_point_type=humidity_data_point_type,
            peripheral=bme280_peripheral,
            parameter_prefix="",
        )
        peripheral = PeripheralComponent.objects.prefetch_related(
            "data_point_type_set"
        ).get(pk=bme280_peripheral.pk)
        self.assertEqual(peripheral.pk, bme280_peripheral.pk)
        self.assertEqual(peripheral.site_entity.pk, bme280_entity.pk)
        self.assertEqual(peripheral.pk, bme280_entity.pk)
        self.assertEqual(peripheral.controller_component.pk, self.esp32_a_controller.pk)
        self.assertEqual(
            peripheral.peripheral_type, PeripheralComponent.PeripheralType.BME280_SENSOR
        )
        self.assertEqual(peripheral.state, PeripheralComponent.State.ADDING)
        self.assertDictEqual(
            peripheral.other_parameters, bme280_peripheral.other_parameters
        )
        self.assertDictContainsSubset(
            peripheral.other_parameters, peripheral.parameters
        )
        self.assertEqual(
            peripheral.parameters[
                f"{temperature_link.parameter_prefix}_data_point_type"
            ],
            str(temperature_data_point_type.pk),
        )
        self.assertEqual(
            peripheral.parameters[f"{pressure_link.parameter_prefix}_data_point_type"],
            str(pressure_data_point_type.pk),
        )
        self.assertEqual(
            peripheral.parameters["data_point_type"], str(humidity_data_point_type.pk)
        )

    def test_other_parameter_validation(self):
        """Test that storing data point type parameters in other parameters fails"""

        with self.assertRaises(ValueError):
            PeripheralComponent.objects.create_with_new_site_enitity_and_send(
                name="LED 22",
                site_id=self.site_a.pk,
                controller_component_id=self.esp32_a_controller.pk,
                peripheral_type=PeripheralComponent.PeripheralType.PWM.value,
                other_parameters={"data_point_type": "value"},
                data_point_type_edges=[],
            )


class PeripheralModelResultRegisterTests(TestCase):
    """Test the handling of result messages"""

    def setUp(self):
        """Create two peripherals in the adding state and two in the removing state"""

        self.site_a = Site.objects.create(
            name="Site A",
            owner=get_user_model().objects.create_user(
                email="owner@bar.com",
                password="foo",
            ),
        )
        self.esp32_type = ControllerComponentType.objects.create(name="ESP32")
        self.esp32_a_controller = ControllerComponent.objects.create(
            component_type=self.esp32_type,
            site_entity=SiteEntity.objects.create(name="ESP32 A", site=self.site_a),
        )
        self.peripheral_a = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(
                name="Peripheral A", site=self.site_a
            ),
            peripheral_type=PeripheralComponent.PeripheralType.PWM.value,
            controller_component=self.esp32_a_controller,
            state=PeripheralComponent.State.ADDING.value,
        )
        self.peripheral_b = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(
                name="Peripheral B", site=self.site_a
            ),
            peripheral_type=PeripheralComponent.PeripheralType.PWM.value,
            controller_component=self.esp32_a_controller,
            state=PeripheralComponent.State.ADDING.value,
        )
        self.peripheral_c = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(
                name="Peripheral C", site=self.site_a
            ),
            peripheral_type=PeripheralComponent.PeripheralType.PWM.value,
            controller_component=self.esp32_a_controller,
            state=PeripheralComponent.State.REMOVING.value,
        )
        self.peripheral_d = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(
                name="Peripheral D", site=self.site_a
            ),
            peripheral_type=PeripheralComponent.PeripheralType.PWM.value,
            controller_component=self.esp32_a_controller,
            state=PeripheralComponent.State.REMOVING.value,
        )

    def test_result_success_handling(self):
        """Test the handling of peripheral result messages"""

        # Send success results to all peripherals (add and remove respectively)
        data = {
            "add": [
                {"uuid": str(self.peripheral_a.pk), "status": "success"},
                {"uuid": str(self.peripheral_b.pk), "status": "success"},
            ],
            "remove": [
                {"uuid": str(self.peripheral_c.pk), "status": "success"},
                {"uuid": str(self.peripheral_d.pk), "status": "success"},
            ],
        }
        PeripheralComponent.objects.from_results(data)

        # Expect all peripherals to have changed state
        self.peripheral_a = PeripheralComponent.objects.get(pk=self.peripheral_a.pk)
        self.peripheral_b = PeripheralComponent.objects.get(pk=self.peripheral_b.pk)
        self.peripheral_c = PeripheralComponent.objects.get(pk=self.peripheral_c.pk)
        self.peripheral_d = PeripheralComponent.objects.get(pk=self.peripheral_d.pk)

        self.assertEqual(self.peripheral_a.state, PeripheralComponent.State.ADDED.value)
        self.assertEqual(self.peripheral_b.state, PeripheralComponent.State.ADDED.value)
        self.assertEqual(
            self.peripheral_c.state, PeripheralComponent.State.REMOVED.value
        )
        self.assertEqual(
            self.peripheral_d.state, PeripheralComponent.State.REMOVED.value
        )

    def test_result_success_fail_handling(self):
        """Test that fail and success results are handled correctly"""

        data = {
            "add": [
                {"uuid": str(self.peripheral_a.pk), "status": "success"},
                {"uuid": str(self.peripheral_b.pk), "status": "fail", "detail": "ABC"},
            ],
            "remove": [
                {"uuid": str(self.peripheral_c.pk), "status": "success"},
                {"uuid": str(self.peripheral_d.pk), "status": "fail", "detail": "DEF"},
            ],
        }
        PeripheralComponent.objects.from_results(data)

        # Expect all peripherals to have changed state
        self.peripheral_a = PeripheralComponent.objects.get(pk=self.peripheral_a.pk)
        self.peripheral_b = PeripheralComponent.objects.get(pk=self.peripheral_b.pk)
        self.peripheral_c = PeripheralComponent.objects.get(pk=self.peripheral_c.pk)
        self.peripheral_d = PeripheralComponent.objects.get(pk=self.peripheral_d.pk)

        self.assertEqual(self.peripheral_a.state, PeripheralComponent.State.ADDED.value)
        self.assertEqual(
            self.peripheral_b.state, PeripheralComponent.State.FAILED.value
        )
        self.assertEqual(
            self.peripheral_c.state, PeripheralComponent.State.REMOVED.value
        )
        self.assertEqual(self.peripheral_d.state, PeripheralComponent.State.ADDED.value)

    def test_commands_from_register(self):
        """Test the commands that are generated from a registration request"""

        # Create peripherals to be tested
        self.peripheral_a.state = PeripheralComponent.State.ADDING.value
        self.peripheral_b.state = PeripheralComponent.State.ADDED.value
        self.peripheral_c.state = PeripheralComponent.State.ADDED.value
        self.peripheral_d.state = PeripheralComponent.State.FAILED.value
        PeripheralComponent.objects.bulk_update(
            [
                self.peripheral_a,
                self.peripheral_b,
                self.peripheral_c,
                self.peripheral_d,
            ],
            ["state"],
        )
        added_peripherals = [str(self.peripheral_c.pk)]

        # Perform query
        commands = PeripheralComponent.objects.commands_from_register(
            added_peripherals, self.esp32_a_controller.pk
        )

        # Check the results
        add_uuids = [peripheral["uuid"] for peripheral in commands.get("add", [])]
        self.assertIn(str(self.peripheral_a.pk), add_uuids)
        self.assertIn(str(self.peripheral_b.pk), add_uuids)
        self.assertNotIn(str(self.peripheral_c.pk), add_uuids)
        self.assertNotIn(str(self.peripheral_d.pk), add_uuids)
