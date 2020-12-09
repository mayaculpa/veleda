import graphene
from graphene_django.filter import DjangoFilterConnectionField

from farms.graphql.nodes import (
    SiteNode,
    SiteEntityNode,
    ControllerComponentNode,
    ControllerComponentTypeNode,
    ControllerTaskNode,
    ControllerTaskEnumNode,
    PeripheralComponentNode,
    DataPointTypeNode,
    DataPointNode,
)

from farms.graphql.mutations import StartControllerTask, RestartControllerTask, StopControllerTask


class Query(object):
    """Query commands for the farms GraphQL schema"""

    site = graphene.relay.Node.Field(SiteNode)
    all_sites = DjangoFilterConnectionField(SiteNode)

    site_entity = graphene.relay.Node.Field(SiteEntityNode)
    all_site_entities = DjangoFilterConnectionField(SiteEntityNode)

    controller_component = graphene.relay.Node.Field(ControllerComponentNode)
    all_controller_components = DjangoFilterConnectionField(ControllerComponentNode)

    controller_component_type = graphene.relay.Node.Field(ControllerComponentTypeNode)
    all_controller_component_types = DjangoFilterConnectionField(
        ControllerComponentTypeNode
    )

    controller_task = graphene.relay.Node.Field(ControllerTaskNode)
    all_controller_tasks = DjangoFilterConnectionField(ControllerTaskNode)
    controller_task_enums = graphene.Field(ControllerTaskEnumNode)

    peripheral_component = graphene.relay.Node.Field(PeripheralComponentNode)
    all_peripheral_components = DjangoFilterConnectionField(PeripheralComponentNode)

    data_point_type = graphene.relay.Node.Field(DataPointTypeNode)
    all_data_point_types = DjangoFilterConnectionField(DataPointTypeNode)

    data_point = graphene.relay.Node.Field(DataPointTypeNode)
    all_data_points = DjangoFilterConnectionField(DataPointNode)

    @staticmethod
    def resolve_controller_task_enums(parent, args):
        return ControllerTaskEnumNode()


class Mutation(object):
    """Mutation commands for the farms GraphQL schema"""

    start_controller_task = StartControllerTask.Field()
    restart_controller_task = RestartControllerTask.Field()
    stop_controller_task = StopControllerTask.Field()