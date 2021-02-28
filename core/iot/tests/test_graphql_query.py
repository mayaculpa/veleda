import json
from datetime import datetime, timedelta, timezone
from functools import reduce

from django.contrib.auth import get_user_model
from iot.models import ControllerComponentType, ControllerTask, PeripheralComponent
from iot.models.controller import ControllerComponent
from iot.models.data_point import DataPoint, DataPointType
from iot.models.site import Site, SiteEntity
from graphene_django.utils.testing import GraphQLTestCase
from graphql_relay.node.node import to_global_id


class QueryTestCase(GraphQLTestCase):
    """Test GraphQL queries"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@bar.com", password="foo"
        )
        self._client.force_login(self.owner)

        self.site = Site.objects.create(name="Site A", owner=self.owner)
        self.controller = ControllerComponent.objects.create(
            component_type=ControllerComponentType.objects.create(name="ESP32"),
            site_entity=SiteEntity.objects.create(name="SomeESP32", site=self.site),
        )
        self.peripheral_a = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.ANALOG_IN,
            site_entity=SiteEntity.objects.create(name="PeriA", site=self.site),
            controller_component=self.controller,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.peripheral_b = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.ANALOG_IN,
            site_entity=SiteEntity.objects.create(name="PeriB", site=self.site),
            controller_component=self.controller,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.data_point_type_a = DataPointType.objects.create(name="dptA", unit="uA")
        self.data_point_type_b = DataPointType.objects.create(name="dptB", unit="uB")
        data_points_a = []
        data_points_b = []
        self.now = datetime.now(tz=timezone.utc)
        for day in range(5):
            for point in range(50):
                dp_time = self.now.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=day, minutes=point * 20)
                value = (1 + day) * (1 + point) - 1
                data_points_a.append(
                    DataPoint(
                        peripheral_component=self.peripheral_a,
                        data_point_type=self.data_point_type_a,
                        value=value,
                        time=dp_time,
                    )
                )
                data_points_b.append(
                    DataPoint(
                        peripheral_component=self.peripheral_b,
                        data_point_type=self.data_point_type_b,
                        value=value * 2,
                        time=dp_time + timedelta(seconds=1),
                    )
                )
        DataPoint.objects.bulk_create(data_points_a)
        DataPoint.objects.bulk_create(data_points_b)

    def test_controller_task_enums(self):
        response = self.query(
            """
            {
                controllerTaskEnums {
                    states{
                        value
                        label
                    }
                    taskTypes {
                        value
                        label
                    }
                }
            }"""
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        output = reduce(dict.get, ["data", "controllerTaskEnums"], content)
        for state in output["states"]:
            self.assertIn(state["value"], ControllerTask.State)
        for task_type in output["taskTypes"]:
            self.assertIn(task_type["value"], ControllerTask.TaskType)

    def test_controller_task_enums(self):
        response = self.query(
            """
            {
                peripheralComponentEnums {
                    states {
                        value
                        label
                    }
                    peripheralTypes {
                        value
                        label
                    }
                }
            }"""
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        output = reduce(dict.get, ["data", "peripheralComponentEnums"], content)
        for state in output["states"]:
            self.assertIn(state["value"], PeripheralComponent.State)
        for peripheral_type in output["peripheralTypes"]:
            self.assertIn(peripheral_type["value"], PeripheralComponent.PeripheralType)

    def test_data_point_day_aggregation(self):
        peripheral_a_gid = to_global_id("PeripheralComponentNode", self.peripheral_a.pk)
        data_point_type_a_gid = to_global_id(
            "DataPointTypeNode", self.data_point_type_a.pk
        )
        from_date = self.now.date()
        before_date = from_date + timedelta(days=3)
        response = self.query(
            f"""
            {{
                dataPointsByDay(
                    peripheralComponent: "{peripheral_a_gid}",
                    dataPointType: "{data_point_type_a_gid}",
                    fromDate: "{from_date.isoformat()}",
                    beforeDate: "{before_date.isoformat()}") {{
                        day
                        avg
                        min
                        max
                }}
            }}
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["dataPointsByDay"]
        day_one_dp = next(
            data_point
            for data_point in content
            if data_point["day"] == from_date.isoformat()
        )
        self.assertEqual(day_one_dp["avg"], 24.5)
        self.assertEqual(day_one_dp["min"], 0)
        self.assertEqual(day_one_dp["max"], 49.0)

    def test_data_point_hour_aggregation(self):
        peripheral_b_gid = to_global_id("PeripheralComponentNode", self.peripheral_b.pk)
        data_point_type_b_gid = to_global_id(
            "DataPointTypeNode", self.data_point_type_b.pk
        )
        hour_one = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        hour_ten = hour_one + timedelta(hours=9)
        response = self.query(
            f"""
            {{
                dataPointsByHour(
                    peripheralComponent: "{peripheral_b_gid}",
                    dataPointType: "{data_point_type_b_gid}",
                    fromTime: "{hour_one.isoformat()}",
                    beforeTime: "{(hour_ten + timedelta(hours=10)).isoformat()}") {{
                        timeHour
                        avg
                        min
                        max
                }}
            }}
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["dataPointsByHour"]
        hour_ten_dp = next(
            data_point
            for data_point in content
            if data_point["timeHour"] == hour_ten.isoformat()
        )
        self.assertEqual(hour_ten_dp["avg"], 56.0)
        self.assertEqual(hour_ten_dp["min"], 54.0)
        self.assertEqual(hour_ten_dp["max"], 58.0)
