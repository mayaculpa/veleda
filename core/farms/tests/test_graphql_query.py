import json
from functools import reduce

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model

from farms.models import ControllerTask, PeripheralComponent


class QueryTestCase(GraphQLTestCase):
    """Test GraphQL queries"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@bar.com", password="foo"
        )
        self._client.force_login(self.owner)

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

