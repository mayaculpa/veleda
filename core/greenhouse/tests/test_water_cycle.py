from greenhouse.models.hydroponic_system import HydroponicSystemComponent
from unittest import mock
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from greenhouse.models.water_cycle import (
    WaterCycle,
    WaterCycleComponent,
    WaterCycleComponentException,
    WaterCycleComponentType,
    WaterPipe,
    WaterPump,
    WaterReservoir,
    WaterSensor,
    WaterValve,
)
from iot.models import (
    ControllerComponent,
    ControllerComponentType,
    ControllerTask,
    DataPoint,
    DataPointType,
    PeripheralComponent,
    Site,
    SiteEntity,
)


class WaterCycleComponentTestsBase(TestCase):
    def setUp(self):
        self.site_entity = SiteEntity.objects.create(
            name="SomeWaterPump",
            site=Site.objects.create(
                name="SiteA",
                owner=get_user_model().objects.create_user(
                    email="owner@bar.com", password="foo"
                ),
            ),
        )
        PeripheralComponent.objects.create(
            site_entity=self.site_entity,
            controller_component=ControllerComponent.objects.create(
                site_entity=SiteEntity.objects.create(
                    name="SomeController", site=self.site_entity.site
                ),
                component_type=ControllerComponentType.objects.create(
                    name="MaxController"
                ),
                channel_name="Hi",
            ),
            peripheral_type=PeripheralComponent.PeripheralType.DIGITAL_OUT,
            state=PeripheralComponent.State.ADDED,
        )
        WaterCycleComponent.objects.create(
            site_entity=self.site_entity,
            water_cycle=WaterCycle.objects.create(
                name="SomeCycle", site=self.site_entity.site
            ),
        )
        self.site_entity = SiteEntity.objects.get(pk=self.site_entity.pk)
        self.data_point_type = DataPointType.objects.create(name="SomeDPT", unit="mT")
        self.site_entity.peripheral_component.data_point_type_set.add(
            self.data_point_type
        )
        self.site_entity.save()

    def create_hydroponic_system(self) -> HydroponicSystemComponent:
        """Add a hydroponic system component to the site entity."""

        return HydroponicSystemComponent.objects.create(
            site_entity=self.site_entity,
            hydroponic_system_type=HydroponicSystemComponent.HydroponicSystemType.NFT,
        )

    def create_water_reservoir(self) -> WaterReservoir:
        """Add a water reservoir to the water cycle component."""

        return WaterReservoir.objects.create(
            water_cycle_component=self.site_entity.water_cycle_component,
            max_capacity=700,
            max_water_level=500,
        )

    def create_water_pipe(self) -> WaterPipe:
        """Add a water pipe to the water cycle component."""

        return WaterPipe.objects.create(
            water_cycle_component=self.site_entity.water_cycle_component, length=2.5
        )

    def create_water_pump(self) -> WaterPump:
        """Add a water pump instance to the water cycle component."""

        return WaterPump.objects.create(
            water_cycle_component=self.site_entity.water_cycle_component
        )

    def create_water_sensor(self, **kwargs) -> WaterSensor:
        """Add a water sensor instance to the water cycle component."""

        return WaterSensor.objects.create(
            water_cycle_component=self.site_entity.water_cycle_component, **kwargs
        )

    def create_water_valve(self) -> WaterValve:
        """Add a water valve instance to the water cycle component."""

        return WaterValve.objects.create(
            water_cycle_component=self.site_entity.water_cycle_component
        )


@mock.patch("greenhouse.models.water_cycle.ControllerTask.objects")
class WaterCycleComponentControllerTaskTests(WaterCycleComponentTestsBase):
    """Test water cycle component actions that create controller tasks."""

    def test_water_pump_turn_on(self, magic_controller_task_manager):
        """Test the water pump turning on"""

        water_pump = self.create_water_pump()
        water_pump.turn_on()
        magic_controller_task_manager.start.assert_called_once_with(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.SET_VALUE,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "value": 1,
            },
        )

    def test_water_pump_turn_off(self, magic_controller_task_manager):
        """Test the water pump turning off"""

        water_pump = self.create_water_pump()
        water_pump.turn_off()
        magic_controller_task_manager.start.assert_called_once_with(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.SET_VALUE,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "value": 0,
            },
        )

    def test_water_pump_set_power(self, magic_controller_task_manager):
        """Test setting the water pump to a custom power level"""

        water_pump = self.create_water_pump()
        water_pump.set_power(0.5)
        magic_controller_task_manager.start.assert_called_once_with(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.SET_VALUE,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "value": 0.5,
            },
        )

    def test_open_water_valve(self, magic_controller_task_manager):
        """Test opening a water valve"""

        self.create_water_valve()
        self.site_entity.water_cycle_component.water_valve.open_valve()
        magic_controller_task_manager.start.assert_called_once_with(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.SET_VALUE,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "value": 1,
            },
        )

    def test_close_water_valve(self, magic_controller_task_manager):
        """Test closing a water valve"""

        self.create_water_valve()
        self.site_entity.water_cycle_component.water_valve.close_valve()
        magic_controller_task_manager.start.assert_called_once_with(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.SET_VALUE,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "value": 0,
            },
        )

    def test_water_valve_set_state(self, magic_controller_task_manager):
        """Test opening a water valve"""

        self.create_water_valve()
        self.site_entity.water_cycle_component.water_valve.set_valve_state(True)
        magic_controller_task_manager.start.assert_called_once_with(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.SET_VALUE,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "value": 1,
            },
        )

    def test_water_sensor_request_reading(self, magic_controller_task_manager):
        """Test requesting a sensor reading"""

        self.create_water_sensor()
        dpt_2 = DataPointType.objects.create(name="FooDPT", unit="uS")
        self.site_entity.peripheral_component.data_point_type_set.add(dpt_2)

        self.site_entity.water_cycle_component.water_sensor.request_reading()
        magic_controller_task_manager.start.assert_any_call(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.READ_SENSOR,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
            },
        )
        magic_controller_task_manager.start.assert_any_call(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.READ_SENSOR,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(dpt_2.pk),
            },
        )
        self.assertEqual(2, magic_controller_task_manager.start.call_count)

    def test_water_sensor_start_polling(self, magic_controller_task_manager):
        """Test requesting a sensor to be polled"""

        self.create_water_sensor()
        dpt_2 = DataPointType.objects.create(name="FooDPT", unit="uS")
        self.site_entity.peripheral_component.data_point_type_set.add(dpt_2)
        poll_interval = timedelta(milliseconds=400)
        run_until = datetime.now(tz=timezone.utc) + timedelta(hours=1)

        self.site_entity.water_cycle_component.water_sensor.start_polling_until(
            interval=poll_interval, run_until=run_until
        )
        magic_controller_task_manager.start.assert_any_call(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.POLL_SENSOR,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(dpt_2.pk),
                "interval_ms": int(poll_interval.total_seconds() * 1000),
            },
            run_until,
        )
        magic_controller_task_manager.start.assert_any_call(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.POLL_SENSOR,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "interval_ms": int(poll_interval.total_seconds() * 1000),
            },
            run_until,
        )
        self.assertEqual(2, magic_controller_task_manager.start.call_count)


class WaterCycleComponentTests(WaterCycleComponentTestsBase):
    """Test the different Water Cycle Component aspects"""

    def test_water_pump_multiple_data_point_types(self):
        """Test that an exception is raised when a peripheral has multiple data point types."""

        water_pump = self.create_water_pump()
        data_point_type = DataPointType.objects.create(name="GoDPT", unit="sU")
        self.site_entity.peripheral_component.data_point_type_set.add(data_point_type)
        with self.assertRaises(WaterCycleComponentException):
            water_pump.set_power(0.5)

    def test_water_pump_power(self):
        """Test that the value of the newest data point is returned."""

        water_pump = self.create_water_pump()
        self.assertEqual(None, water_pump.power)

        start_time = datetime.now(tz=timezone.utc)
        data_points = [
            DataPoint(
                time=start_time + timedelta(minutes=i),
                peripheral_component=self.site_entity.peripheral_component,
                data_point_type=self.data_point_type,
                value=i,
            )
            for i in range(-1, 2)
        ]
        DataPoint.objects.bulk_create(data_points)
        self.assertEqual(data_points[-1].value, water_pump.power)

    def test_water_valve_multiple_data_point_types(self):
        """Test that an exception is raised when a peripheral has multiple data point types."""

        self.create_water_valve()
        data_point_type = DataPointType.objects.create(name="GoDPT", unit="sU")
        self.site_entity.peripheral_component.data_point_type_set.add(data_point_type)
        with self.assertRaises(WaterCycleComponentException):
            self.site_entity.water_cycle_component.water_valve.set_valve_state(True)

    def test_water_cycle_component_types(self):
        """Test that the types of water cycle components are returned correctly"""

        types = self.site_entity.water_cycle_component.get_types()
        self.assertFalse(types)

        self.create_hydroponic_system()
        types = self.site_entity.water_cycle_component.get_types()
        self.assertIn(WaterCycleComponentType.HYDROPONIC_SYSTEM, types)

        self.create_water_reservoir()
        types = self.site_entity.water_cycle_component.get_types()
        self.assertIn(WaterCycleComponentType.WATER_RESERVOIR, types)

        self.create_water_pipe()
        types = self.site_entity.water_cycle_component.get_types()
        self.assertIn(WaterCycleComponentType.WATER_PIPE, types)

        self.create_water_pump()
        types = self.site_entity.water_cycle_component.get_types()
        self.assertIn(WaterCycleComponentType.WATER_PUMP, types)

        self.create_water_sensor()
        types = self.site_entity.water_cycle_component.get_types()
        self.assertIn(WaterCycleComponentType.WATER_RESERVOIR, types)

        self.create_water_valve()
        types = self.site_entity.water_cycle_component.get_types()
        self.assertIn(WaterCycleComponentType.WATER_VALVE, types)

        # Check for some of the returned choice values and labels
        type_values = self.site_entity.water_cycle_component.get_type_values()
        self.assertIn(WaterCycleComponentType.WATER_PIPE.value, type_values)
        self.assertIn(WaterCycleComponentType.HYDROPONIC_SYSTEM.value, type_values)

        type_labels = self.site_entity.water_cycle_component.get_type_labels()
        self.assertIn(WaterCycleComponentType.WATER_PUMP.label, type_labels)
        self.assertIn(WaterCycleComponentType.WATER_RESERVOIR.label, type_labels)

        self.assertIn(
            self.site_entity.name, str(self.site_entity.water_cycle_component)
        )


class WaterCycleTests(TestCase):
    """Tests for the water cycle model."""
    
    def test_water_cycle_name(self):
        """Test to string for water cycles"""

        name = "Some Cycle"
        site = Site.objects.create(
            name="SiteA",
            owner=get_user_model().objects.create_user(
                email="owner@bar.com", password="foo"
            ),
        )
        water_cycle = WaterCycle.objects.create(name=name, site=site)
        self.assertIn(name, str(water_cycle))
