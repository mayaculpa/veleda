import json
from functools import reduce
from django.contrib.auth import get_user_model
from graphene_django.utils.testing import GraphQLTestCase
from graphql_relay import to_global_id

from greenhouse.models.water_cycle import (
    WaterCycle,
    WaterCycleComponent,
    WaterPump,
    WaterValve,
)
from greenhouse.graphql.nodes import WaterCycleComponentNode
from iot.models import (
    ControllerComponent,
    ControllerComponentType,
    DataPointType,
    PeripheralComponent,
    Site,
    SiteEntity,
)


class WaterCycleComponentTestCases(GraphQLTestCase):
    """Tests the mutation commands for the controller tasks"""

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
        self._client.force_login(self.site_entity.site.owner)
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
        self.water_cycle_component_gid = to_global_id(
            WaterCycleComponentNode._meta.name, self.site_entity.pk
        )

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

    def test_turn_on_water_pump(self):
        """Test turning on the water pump"""

        self.create_water_pump()
        input_data = {"waterCycleComponent": self.water_cycle_component_gid}
        response = self.query(
            """
            mutation turnOnWaterPump($input: TurnOnWaterPumpInput!) {
                turnOnWaterPump(input: $input) {
                    errors { message }
                }
            }
            """,
            op_name="turnOnWaterPump",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertFalse(content["data"]["turnOnWaterPump"]["errors"])

    def test_turn_off_water_pump(self):
        """Test turning on the water pump"""

        self.create_water_pump()
        input_data = {"waterCycleComponent": self.water_cycle_component_gid}
        response = self.query(
            """
            mutation turnOffWaterPump($input: TurnOffWaterPumpInput!) {
                turnOffWaterPump(input: $input) {
                    errors { message }
                }
            }
            """,
            op_name="turnOffWaterPump",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertFalse(content["data"]["turnOffWaterPump"]["errors"])

    def test_set_water_pump_power(self):
        """Test turning on the water pump"""

        self.create_water_pump()
        input_data = {
            "waterCycleComponent": self.water_cycle_component_gid,
            "power": 0.5,
        }
        response = self.query(
            """
            mutation setWaterPumpPower($input: SetWaterPumpPowerInput!) {
                setWaterPumpPower(input: $input) {
                    errors { message }
                }
            }
            """,
            op_name="setWaterPumpPower",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertFalse(content["data"]["setWaterPumpPower"]["errors"])

    def test_open_water_valve(self):
        """Test opening a water valve"""

        self.create_water_valve()
        input_data = {"waterCycleComponent": self.water_cycle_component_gid}
        response = self.query(
            """
            mutation openWaterValve($input: OpenWaterValveInput!) {
                openWaterValve(input: $input) {
                    errors { message }
                }
            }
            """,
            op_name="openWaterValve",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertFalse(content["data"]["openWaterValve"]["errors"])

    def test_close_water_valve(self):
        """Test closing a water valve"""

        self.create_water_valve()
        input_data = {"waterCycleComponent": self.water_cycle_component_gid}
        response = self.query(
            """
            mutation closeWaterValve($input: CloseWaterValveInput!) {
                closeWaterValve(input: $input) {
                    errors { message }
                }
            }
            """,
            op_name="closeWaterValve",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertFalse(content["data"]["closeWaterValve"]["errors"])
