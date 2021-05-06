import uuid

import graphene
from graphene import relay
from graphql_relay import from_global_id
from graphql import GraphQLError

from iot.graphql.nodes import (
    ControllerAuthTokenNode,
    ControllerComponentNode,
    ControllerTask,
    ControllerTaskNode,
    PeripheralComponent,
    PeripheralComponentNode,
)
from iot.models import ControllerComponent


class Error(graphene.Interface):
    message = graphene.String(required=True)


class CreateControllerComponent(relay.ClientIDMutation):
    """Mutation to create a new controller component."""

    class Input:
        name = graphene.String(required=True)
        site = graphene.ID(required=True)
        controller_type = graphene.ID(required=True)

    controller_component = graphene.Field(ControllerComponentNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        name = kwargs["name"]
        site_id = uuid.UUID(from_global_id(kwargs["site"])[1])
        controller_type_id = from_global_id(kwargs["controller_type"])[1]
        try:
            controller_component = ControllerComponent.objects.create_controller(
                name, site_id, controller_type_id
            )
        except ValueError as err:
            raise GraphQLError(str(err)) from err
        return cls(controller_component=controller_component)


class CycleControllerAuthToken(relay.ClientIDMutation):
    """Mutation to cycle a controller's auth token."""

    class Input:
        controller = graphene.ID(required=True)

    controller_auth_token = graphene.Field(ControllerAuthTokenNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        pk = from_global_id(kwargs["controller"])[1]
        controller_component = ControllerComponent.objects.get(pk)
        controller_auth_token = controller_component.cycle_auth_token()
        return cls(controller_auth_token=controller_auth_token)


class StartControllerTask(relay.ClientIDMutation):
    class Input:
        controller_component = graphene.ID(required=True)
        task_type = graphene.String(required=True)
        parameters = graphene.JSONString(required=True)
        run_until = graphene.DateTime()

    controller_task = graphene.Field(ControllerTaskNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        controller_component_id = from_global_id(kwargs["controller_component"])[1]
        controller_task = ControllerTask.objects.start(
            controller_component_id=controller_component_id,
            task_type=kwargs["task_type"],
            parameters=kwargs["parameters"],
            run_until=kwargs.get("run_until", None),
        )

        return cls(controller_task=controller_task)


class RestartControllerTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)

    controller_task = graphene.Field(ControllerTaskNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        task_id = from_global_id(kwargs["task_id"])[1]
        controller_task = ControllerTask.objects.restart(task_id=task_id)
        return cls(controller_task=controller_task)


class StopControllerTask(relay.ClientIDMutation):
    class Input:
        task_id = graphene.ID(required=True)

    controller_task = graphene.Field(ControllerTaskNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        task_id = from_global_id(kwargs["task_id"])[1]
        controller_task = ControllerTask.objects.stop(task_id=task_id)
        return cls(controller_task=controller_task)


class DataPointTypeEdge(graphene.InputObjectType):
    data_point_type = graphene.ID(required=True)
    parameter_prefix = graphene.String(default_value="")


class CreatePeripheralComponent(relay.ClientIDMutation):
    class Input:
        name = graphene.String(required=True)
        site = graphene.ID(required=True)
        controller_component = graphene.ID(required=True)
        peripheral_type = graphene.String(required=True)
        data_point_type_edges = graphene.List(DataPointTypeEdge)
        other_parameters = graphene.JSONString()

    peripheral_component = graphene.Field(PeripheralComponentNode)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        site_id = uuid.UUID(from_global_id(kwargs["site"])[1])
        controller_component_id = uuid.UUID(
            from_global_id(kwargs["controller_component"])[1]
        )
        other_parameters = kwargs.get("other_parameters", dict)
        data_point_type_edges = {
            uuid.UUID(from_global_id(edge.data_point_type)[1]): edge.parameter_prefix
            for edge in kwargs.get("data_point_type_edges", {})
        }
        try:
            peripheral_component = (
                PeripheralComponent.objects.create_with_new_site_enitity_and_send(
                    name=kwargs["name"],
                    site_id=site_id,
                    controller_component_id=controller_component_id,
                    peripheral_type=kwargs["peripheral_type"],
                    other_parameters=other_parameters,
                    data_point_type_edges=data_point_type_edges,
                )
            )
        except ValueError as err:
            raise GraphQLError(str(err)) from err
        return cls(peripheral_component=peripheral_component)
