from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from greenhouse.models.water_cycle import (
    WaterCycle,
    WaterCycleComponent,
    WaterPump,
    WaterValve,
)
from iot.models import (
    ControllerComponent,
    ControllerComponentType,
    ControllerTask,
    DataPointType,
    PeripheralComponent,
    Site,
    SiteEntity,
)


@mock.patch("greenhouse.models.water_cycle.ControllerTask.objects")
class WaterCycleComponentTests(TestCase):
    """Test the different Water Cycle Component aspects"""

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
            water_cycle=WaterCycle.objects.create(name="SomeCycle"),
        )
        self.site_entity = SiteEntity.objects.get(pk=self.site_entity.pk)
        self.data_point_type = DataPointType.objects.create(name="SomeDPT", unit="mT")
        self.site_entity.peripheral_component.data_point_type_set.add(
            self.data_point_type
        )
        self.site_entity.save()

    def create_water_pump(self):
        """Add a water pump instance to the water cycle component"""

        WaterPump.objects.create(
            water_cycle_component=self.site_entity.water_cycle_component
        )

    def create_water_valve(self):
        """Add a water valve instance to the water cycle component"""

        WaterValve.objects.create(
            water_cycle_component=self.site_entity.water_cycle_component
        )

    def test_water_pump_turn_on(self, magic_controller_task_manager):
        """Test the water pump turning on"""

        self.create_water_pump()
        self.site_entity.water_cycle_component.water_pump.turn_on()
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

        self.create_water_pump()
        self.site_entity.water_cycle_component.water_pump.turn_off()
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

        self.create_water_pump()
        self.site_entity.water_cycle_component.water_pump.set_power(0.5)
        magic_controller_task_manager.start.assert_called_once_with(
            self.site_entity.peripheral_component.controller_component.pk,
            ControllerTask.TaskType.SET_VALUE,
            {
                "peripheral": str(self.site_entity.peripheral_component.pk),
                "data_point_type": str(self.data_point_type.pk),
                "value": 0.5,
            },
        )

    def test_water_valve_open(self, magic_controller_task_manager):
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

    def test_water_valve_close(self, magic_controller_task_manager):
        """Test opening a water valve"""

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