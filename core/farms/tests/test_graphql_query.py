import json
from functools import reduce

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model

from farms.models import ControllerTask


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
            query {
                controllerTaskEnums{
                    stateValues
                    stateLabels
                    taskTypeValues
                    taskTypeLabels
                }
            }"""
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        output = reduce(dict.get, ["data", "controllerTaskEnums"], content)
        for state in ControllerTask.State:
            self.assertIn(state.value, output["stateValues"])
            self.assertIn(state.label, output["stateLabels"])
        for task_type in ControllerTask.TaskType:
            self.assertIn(task_type.value, output["taskTypeValues"])
            self.assertIn(task_type.label, output["taskTypeLabels"])
