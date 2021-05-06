import graphene
from graphene_django.filter import DjangoFilterConnectionField

from iot.graphql.nodes import (
    FirmwareImageNode,
    SiteNode,
    SiteEntityNode,
    ControllerComponentNode,
    ControllerComponentTypeNode,
    ControllerTaskNode,
    ControllerTaskEnumNode,
    PeripheralComponentNode,
    PeripheralComponentEnumNode,
    DataPointTypeNode,
    DataPointNode,
    DataPointByDayNode,
    DataPointByHourNode,
)

from iot.graphql.mutations import (
    CreateControllerComponent,
    CycleControllerAuthToken,
    StartControllerTask,
    RestartControllerTask,
    StopControllerTask,
    CreatePeripheralComponent,
)

from iot.graphql.subscriptions import (
    ControllerMessageSubscription,
    DataPointSubscription,
)


class Query:
    """Query commands for the iot GraphQL schema"""

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
    peripheral_component_enums = graphene.Field(PeripheralComponentEnumNode)

    data_point_type = graphene.relay.Node.Field(DataPointTypeNode)
    all_data_point_types = DjangoFilterConnectionField(DataPointTypeNode)

    data_point = graphene.relay.Node.Field(DataPointTypeNode)
    all_data_points = DjangoFilterConnectionField(DataPointNode)

    data_points_by_day = DataPointByDayNode.as_list_field()
    data_points_by_hour = DataPointByHourNode.as_list_field()

    firmware_image = graphene.relay.Node.Field(FirmwareImageNode)
    all_firmware_images = DjangoFilterConnectionField(FirmwareImageNode)

    @staticmethod
    def resolve_controller_task_enums(parent, args):
        return ControllerTaskEnumNode()

    @staticmethod
    def resolve_peripheral_component_enums(parent, args):
        return PeripheralComponentEnumNode()

    @staticmethod
    def resolve_data_points_by_day(parent, info, **kwargs):
        return DataPointByDayNode.resolve(parent, info, **kwargs)

    @staticmethod
    def resolve_data_points_by_hour(parent, info, **kwargs):
        return DataPointByHourNode.resolve(parent, info, **kwargs)


class Mutation:
    """Mutation commands for the iot GraphQL schema"""

    create_controller_component = CreateControllerComponent.Field()
    cycle_controller_auth_token = CycleControllerAuthToken.Field()

    start_controller_task = StartControllerTask.Field()
    restart_controller_task = RestartControllerTask.Field()
    stop_controller_task = StopControllerTask.Field()

    create_peripheral_component = CreatePeripheralComponent.Field()


class Subscription(graphene.ObjectType):
    """Root GraphQL subscription."""

    data_point_subscription = DataPointSubscription.Field()
    controller_message_subscription = ControllerMessageSubscription.Field()
