import json
from functools import reduce

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from farms.graphql.nodes import ControllerComponentNode, ControllerTaskNode
from farms.models import (
    ControllerTask,
    ControllerComponent,
    ControllerComponentType,
    SiteEntity,
    Site,
)


class MutationTestCase(GraphQLTestCase):
    """Tests the mutation commands in the GraphQL interface"""

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