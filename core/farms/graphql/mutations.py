import graphene
from graphene import relay
from graphql_relay import from_global_id

from farms.graphql.nodes import (
    ControllerTask,
    ControllerTaskNode,
    PeripheralComponentNode,
)


class StartControllerTask(relay.ClientIDMutation):
    class Input:
        controller_component = graphene.ID(required=True)
        task_type = graphene.String(required=True)
        parameters = graphene.JSONString(required=True)
        run_until = graphene.DateTime()

    controller_task = graphene.Field(ControllerTaskNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        try:
            controller_task = ControllerTask.objects.start(
                controller_component_id=from_global_id(kwargs["controller_component"])[
                    1
                ],
                task_type=kwargs["task_type"],
                parameters=kwargs["parameters"],
                run_until=kwargs.get("run_until", None),
            )
        except KeyError as err:
            raise Exception(f"Key not found: {err}") from err

        return StartControllerTask(controller_task=controller_task)


class RestartControllerTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)

    controller_task = graphene.Field(ControllerTaskNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        try:
            task_id = from_global_id(kwargs["task_id"])[1]
        except KeyError as err:
            raise Exception(f"Key not found: {err}") from err
        controller_task = ControllerTask.objects.restart(task_id=task_id)
        return StopControllerTask(controller_task=controller_task)


class StopControllerTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)

    controller_task = graphene.Field(ControllerTaskNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        try:
            task_id = from_global_id(kwargs["task_id"])[1]
        except KeyError as err:
            raise Exception(f"Key not found: {err}") from err
        controller_task = ControllerTask.objects.stop(task_id=task_id)
        return StopControllerTask(controller_task=controller_task)


