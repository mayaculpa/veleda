import json
from datetime import datetime, timezone, timedelta
from functools import reduce

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from farms.graphql.nodes import (
    ControllerComponentNode,
    ControllerTaskNode,
    DataPointTypeNode,
    SiteNode,
)
from farms.models import (
    ControllerTask,
    ControllerComponent,
    ControllerComponentType,
    DataPointType,
    PeripheralComponent,
    SiteEntity,
    Site,
)


class ControllerTaskTestCase(GraphQLTestCase):
    """Tests the mutation commands for the controller tasks"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@bar.com", password="foo"
        )
        self._client.force_login(self.owner)
        self.controller_a = ControllerComponent.objects.create(
            component_type=ControllerComponentType.objects.create(name="TypeA"),
            site_entity=SiteEntity.objects.create(
                name="ControllerA",
                site=Site.objects.create(
                    name="SiteA",
                    owner=self.owner,
                ),
            ),
            channel_name="some_channel",
        )
        self.controller_a_gid = to_global_id(
            ControllerComponentNode._meta.name, self.controller_a.pk
        )

    def test_starting_controller_task(self):
        """Test the creation and starting of a controller task"""

        input_data = {
            "controllerComponent": self.controller_a_gid,
            "taskType": ControllerTask.TaskType.WRITE_ACTUATOR.value,
            "parameters": '{"some": "parameter"}',
            "runUntil": (
                datetime.now(tz=timezone.utc) + timedelta(minutes=1)
            ).isoformat(),
        }
        response = self.query(
            """
            mutation startControllerTask($input: StartControllerTaskInput!) {
                startControllerTask(input: $input) {
                    controllerTask {
                        controllerComponent {
                            id
                        }
                        taskType
                        parameters
                        state
                        runUntil
                    }
                }
            }
            """,
            op_name="startControllerTask",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        output = reduce(
            dict.get, ["data", "startControllerTask", "controllerTask"], content
        )
        self.assertEqual(output["taskType"], input_data["taskType"])
        self.assertEqual(output["parameters"], input_data["parameters"])
        self.assertEqual(output["state"], ControllerTask.State.STARTING.value)
        self.assertEqual(output["controllerComponent"]["id"], self.controller_a_gid)
        self.assertEqual(output["runUntil"], input_data["runUntil"])

    def test_restarting_controller_task(self):
        """Test restarting an existing task"""

        controller_task = ControllerTask.objects.create(
            controller_component=self.controller_a,
            task_type=ControllerTask.TaskType.WRITE_ACTUATOR.value,
            state=ControllerTask.State.STOPPED.value,
            parameters={"some": "parameter"},
        )
        controller_task_gid = to_global_id(
            ControllerTaskNode._meta.name, controller_task.pk
        )
        input_data = {"taskId": controller_task_gid}
        response = self.query(
            """
            mutation restartControllerTask($input: RestartControllerTaskInput!) {
                restartControllerTask(input: $input) {
                    controllerTask {
                        controllerComponent {
                            id
                        }
                        taskType
                        parameters
                        state
                    }
                }
            }
            """,
            op_name="restartControllerTask",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        output = reduce(
            dict.get, ["data", "restartControllerTask", "controllerTask"], content
        )

        self.assertEqual(output["taskType"], controller_task.task_type)
        self.assertDictEqual(
            json.loads(output["parameters"]), controller_task.parameters
        )
        self.assertEqual(output["state"], ControllerTask.State.STARTING.value)
        self.assertEqual(output["controllerComponent"]["id"], self.controller_a_gid)

    def test_stopping_controller_task(self):
        """Test stopping of a running controller task"""

        controller_task = ControllerTask.objects.create(
            controller_component=self.controller_a,
            task_type=ControllerTask.TaskType.WRITE_ACTUATOR.value,
            state=ControllerTask.State.RUNNING.value,
            parameters={"some": "parameter"},
        )
        controller_task_gid = to_global_id(
            ControllerTaskNode._meta.name, controller_task.pk
        )
        input_data = {"taskId": controller_task_gid}
        response = self.query(
            """
            mutation stopControllerTask($input: StopControllerTaskInput!) {
                stopControllerTask(input: $input) {
                    controllerTask {
                        controllerComponent{id}
                        taskType
                        parameters
                        state
                    }
                }
            }
            """,
            op_name="stopControllerTask",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        output = reduce(
            dict.get, ["data", "stopControllerTask", "controllerTask"], content
        )
        self.assertEqual(output["taskType"], controller_task.task_type)
        self.assertDictEqual(
            json.loads(output["parameters"]), controller_task.parameters
        )
        self.assertEqual(output["state"], ControllerTask.State.STOPPING.value)
        self.assertEqual(output["controllerComponent"]["id"], self.controller_a_gid)


class PeripheralControllerTestCase(GraphQLTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@bar.com", password="foo"
        )
        self._client.force_login(self.owner)
        self.controller_a = ControllerComponent.objects.create(
            component_type=ControllerComponentType.objects.create(name="TypeA"),
            site_entity=SiteEntity.objects.create(
                name="ControllerA",
                site=Site.objects.create(
                    name="SiteA",
                    owner=self.owner,
                ),
            ),
            channel_name="some_channel",
        )
        self.controller_a_gid = to_global_id(
            ControllerComponentNode._meta.name, self.controller_a.pk
        )
        self.query_text = """
            mutation createPeripheralComponent($input: CreatePeripheralComponentInput!) {
              createPeripheralComponent(input: $input) {
                peripheralComponent {
                  id
                  siteEntity{id, name}
                  controllerComponent{id}
                  peripheralType
                  state
                  parameters
                }
              }
            }
            """
        self.data_point_type_a = DataPointType.objects.create(name="DPTA", unit="a")
        self.data_point_type_b = DataPointType.objects.create(name="DPTB", unit="b")
        self.data_point_type_c = DataPointType.objects.create(name="DPTC", unit="c")

    def test_creating_peripheral_component(self):
        """Test creating a peripheral component with a new site entity"""

        data_point_type_edges = [
            {
                "dataPointType": to_global_id(
                    DataPointTypeNode._meta.name, self.data_point_type_a.pk
                ),
                "parameterPrefix": "a",
            },
            {
                "dataPointType": to_global_id(
                    DataPointTypeNode._meta.name, self.data_point_type_b.pk
                ),
                "parameterPrefix": "b",
            },
            {
                "dataPointType": to_global_id(
                    DataPointTypeNode._meta.name, self.data_point_type_c.pk
                ),
                "parameterPrefix": "",
            },
        ]
        input_data = {
            "name": "Some name",
            "site": to_global_id(
                SiteNode._meta.name, self.controller_a.site_entity.site.pk
            ),
            "controllerComponent": self.controller_a_gid,
            "peripheralType": PeripheralComponent.PeripheralType.LED.value,
            "dataPointTypeEdges": data_point_type_edges,
            "otherParameters": '{"some": "parameter"}',
        }
        response = self.query(
            self.query_text,
            op_name="createPeripheralComponent",
            input_data=input_data,
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        output = reduce(
            dict.get,
            ["data", "createPeripheralComponent", "peripheralComponent"],
            content,
        )

        output["parameters"] = json.loads(output["parameters"])
        input_data["otherParameters"] = json.loads(input_data["otherParameters"])

        self.assertEqual(output["peripheralType"], input_data["peripheralType"])
        self.assertDictContainsSubset(
            input_data["otherParameters"], output["parameters"]
        )
        self.assertIn("a_data_point_type", output["parameters"])
        self.assertIn("b_data_point_type", output["parameters"])
        self.assertIn("data_point_type", output["parameters"])
        self.assertEqual(output["state"], PeripheralComponent.State.ADDING.value)
        self.assertEqual(output["controllerComponent"]["id"], self.controller_a_gid)

    def test_adding_peripheral_to_newly_created_controller(self):
        """Test that commands cannot be sent to a newly created controller"""

        self.controller_a.channel_name = ""
        self.controller_a.save()

        input_data = {
            "name": "Some name",
            "site": to_global_id(
                SiteNode._meta.name, self.controller_a.site_entity.site.pk
            ),
            "controllerComponent": self.controller_a_gid,
            "peripheralType": PeripheralComponent.PeripheralType.LED.value,
            "dataPointTypeEdges": [],
            "otherParameters": "{}",
        }
        response = self.query(
            self.query_text,
            op_name="createPeripheralComponent",
            input_data=input_data,
        )
        self.assertResponseHasErrors(response)
        self.assertIn(
            "not connected", json.loads(response.content)["errors"][0]["message"]
        )
