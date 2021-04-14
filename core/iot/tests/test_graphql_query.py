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
        self.owner_z = get_user_model().objects.create_user(
            email="ownerB@bar.com", password="foo"
        )
        self._client.force_login(self.owner)

        self.site_a = Site.objects.create(name="Site A", owner=self.owner)
        self.site_z = Site.objects.create(name="Site Z", owner=self.owner_z)
        self.esp32_type = ControllerComponentType.objects.create(name="ESP32")
        self.espXX_type = ControllerComponentType.objects.create(
            name="ESPXX", created_by=self.owner
        )
        self.espZZ_type = ControllerComponentType.objects.create(
            name="ESPZZ", created_by=self.owner_z
        )
        self.controller_a = ControllerComponent.objects.create(
            component_type=self.esp32_type,
            site_entity=SiteEntity.objects.create(name="SomeESP32", site=self.site_a),
        )
        self.controller_z = ControllerComponent.objects.create(
            component_type=self.controller_a.component_type,
            site_entity=SiteEntity.objects.create(name="AnyESP32", site=self.site_z),
        )
        self.peripheral_a = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.ANALOG_IN,
            site_entity=SiteEntity.objects.create(name="PeriA", site=self.site_a),
            controller_component=self.controller_a,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.peripheral_b = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.ANALOG_IN,
            site_entity=SiteEntity.objects.create(name="PeriB", site=self.site_a),
            controller_component=self.controller_a,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.peripheral_z = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.DIGITAL_IN,
            site_entity=SiteEntity.objects.create(name="PeriZ", site=self.site_z),
            controller_component=self.controller_z,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.data_point_type_a = DataPointType.objects.create(name="dptA", unit="uA")
        self.data_point_type_b = DataPointType.objects.create(
            name="dptB", unit="uB", created_by=self.owner
        )
        self.data_point_type_z = DataPointType.objects.create(
            name="dptZ", unit="uZ", created_by=self.owner_z
        )
        self.contrller_task_a = ControllerTask.objects.create(
            controller_component=self.controller_a,
            task_type=ControllerTask.TaskType.READ_SENSOR,
            state=ControllerTask.State.RUNNING,
        )
        self.contrller_task_z = ControllerTask.objects.create(
            controller_component=self.controller_z,
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            state=ControllerTask.State.STOPPED,
        )
        data_points_a = []
        data_points_b = []
        data_points_z = []
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
                data_points_z.append(
                    DataPoint(
                        peripheral_component=self.peripheral_z,
                        data_point_type=self.data_point_type_z,
                        value=value * 3,
                        time=dp_time + timedelta(seconds=2),
                    )
                )
        DataPoint.objects.bulk_create(data_points_a)
        DataPoint.objects.bulk_create(data_points_b)
        DataPoint.objects.bulk_create(data_points_z)

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

    def test_data_point_ordering(self):
        """Test that the ordering is respected."""

        peripheral_gid = to_global_id("PeripheralComponentNode", self.peripheral_a.pk)
        data_point_type_gid = to_global_id(
            "DataPointTypeNode", self.data_point_type_a.pk
        )
        query = """
            {{ allDataPoints(
                orderBy: "{}", peripheralComponent: "{}", dataPointType: "{}"
            ) {{
                edges {{ node {{
                  time, value
                }} }}
            }} }}
            """
        response = self.query(query.format("time", peripheral_gid, data_point_type_gid))
        self.assertResponseNoErrors(response)
        output = json.loads(response.content)["data"]["allDataPoints"]["edges"]
        data_points = [i["node"] for i in output]
        self.assertEqual(data_points[0]["time"], "2021-04-14T00:00:00+00:00")

        response = self.query(
            query.format("-time", peripheral_gid, data_point_type_gid)
        )
        self.assertResponseNoErrors(response)
        output = json.loads(response.content)["data"]["allDataPoints"]["edges"]
        data_points = [i["node"] for i in output]
        self.assertEqual(data_points[0]["time"], "2021-04-18T16:20:00+00:00")

    def test_data_point_day_ordering(self):
        """Test that the ordering is respected."""

        peripheral_gid = to_global_id("PeripheralComponentNode", self.peripheral_a.pk)
        data_point_type_gid = to_global_id(
            "DataPointTypeNode", self.data_point_type_a.pk
        )
        query = """
            {{ dataPointsByDay(
                ascending: {}, peripheralComponent: "{}", dataPointType: "{}"
            ) {{
                day, avg
              }}
            }}
            """
        response = self.query(query.format("true", peripheral_gid, data_point_type_gid))
        self.assertResponseNoErrors(response)
        data_points = json.loads(response.content)["data"]["dataPointsByDay"]
        self.assertEqual(data_points[0]["day"], "2021-04-14")

        response = self.query(
            query.format("false", peripheral_gid, data_point_type_gid)
        )
        self.assertResponseNoErrors(response)
        data_points = json.loads(response.content)["data"]["dataPointsByDay"]
        self.assertEqual(data_points[0]["day"], "2021-04-18")

    def test_data_point_hour_ordering(self):
        """Test that the ordering is respected."""

        peripheral_gid = to_global_id("PeripheralComponentNode", self.peripheral_a.pk)
        data_point_type_gid = to_global_id(
            "DataPointTypeNode", self.data_point_type_a.pk
        )
        query = """
            {{ dataPointsByHour(
                ascending: {}, peripheralComponent: "{}", dataPointType: "{}"
            ) {{
                timeHour, avg
              }}
            }}
            """
        response = self.query(query.format("true", peripheral_gid, data_point_type_gid))
        self.assertResponseNoErrors(response)
        data_points = json.loads(response.content)["data"]["dataPointsByHour"]
        self.assertEqual(data_points[0]["timeHour"], "2021-04-14T00:00:00+00:00")

        response = self.query(
            query.format("false", peripheral_gid, data_point_type_gid)
        )
        self.assertResponseNoErrors(response)
        data_points = json.loads(response.content)["data"]["dataPointsByHour"]
        self.assertEqual(data_points[0]["timeHour"], "2021-04-18T16:00:00+00:00")

    def test_site_isolation(self):
        """Check that queries are isolated according to sites"""

        response = self.query("{allSites{edges{node{id, name}}}}")
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allSites"]["edges"]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["node"]["name"], self.site_a.name)
        self.assertEqual(Site.objects.all().count(), 2)

        response = self.query("{allSiteEntities{edges{node{id, name}}}}")
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allSiteEntities"]["edges"]
        self.assertEqual(len(nodes), 3)
        self.assertEqual(SiteEntity.objects.all().count(), 5)

        response = self.query("{allControllerComponents{edges{node{id}}}}")
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allControllerComponents"]["edges"]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(ControllerComponent.objects.all().count(), 2)

        response = self.query("{allPeripheralComponents{edges{node{id}}}}")
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allPeripheralComponents"]["edges"]
        self.assertEqual(len(nodes), 2)
        self.assertEqual(PeripheralComponent.objects.all().count(), 3)

        response = self.query("{allControllerComponentTypes{edges{node{name}}}}")
        self.assertResponseNoErrors(response)
        json_data = json.loads(response.content)["data"]
        nodes = json_data["allControllerComponentTypes"]["edges"]
        self.assertEqual(len(nodes), 2)
        self.assertEqual(ControllerComponentType.objects.all().count(), 3)

        response = self.query("{allControllerTasks{edges{node{state}}}}")
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allControllerTasks"]["edges"]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(ControllerTask.objects.all().count(), 2)

        response = self.query("{allDataPointTypes{edges{node{name}}}}")
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allDataPointTypes"]["edges"]
        self.assertEqual(len(nodes), 2)
        self.assertEqual(DataPointType.objects.all().count(), 3)

        gid = to_global_id("PeripheralComponentNode", self.peripheral_a.pk)
        query = (
            '{{allDataPoints(peripheralComponent: "{gid}"){{edges{{node{{value}}}}}}}}'
        )
        response = self.query(query.format(gid=gid))
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allDataPoints"]["edges"]
        self.assertTrue(nodes)

        gid = to_global_id("PeripheralComponentNode", self.peripheral_z.pk)
        response = self.query(query.format(gid=gid))
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allDataPoints"]["edges"]
        self.assertFalse(nodes)

        # Changes logged in user. Test last
        self._client.force_login(self.owner_z)
        gid = to_global_id("PeripheralComponentNode", self.peripheral_z.pk)
        response = self.query(query.format(gid=gid))
        self.assertResponseNoErrors(response)
        nodes = json.loads(response.content)["data"]["allDataPoints"]["edges"]
        self.assertTrue(nodes)
