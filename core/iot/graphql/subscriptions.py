import graphene
from channels_graphql_ws import Subscription
from graphql_relay import from_global_id

from iot.graphql.nodes import ControllerMessageNode, DataPointNode
from iot.models import ControllerMessage, DataPoint


class DataPointSubscription(Subscription):
    """GraphQL subscription for data points."""

    data_point = graphene.Field(DataPointNode)

    class Arguments:
        """Specify a list of peripheral and/or data point type IDs."""

        peripheral_ids = graphene.List(graphene.ID, required=False)
        data_point_type_ids = graphene.List(graphene.ID, required=False)

    @classmethod
    def subscribe(cls, root, info, **kwargs):
        """Called when user subscribes."""

        topics = []

        if peripheral_ids := kwargs.get("peripheral_ids"):
            topics.extend(
                [cls._to_data_point_group(from_global_id(i)[1]) for i in peripheral_ids]
            )
        if data_point_type_ids := kwargs.get("data_point_type_ids"):
            topics.extend(
                [
                    cls._to_data_point_group(from_global_id(i)[1])
                    for i in data_point_type_ids
                ]
            )

        if topics:
            return topics
        return None

    @classmethod
    def publish(cls, payload, info, **kwargs):
        """Called to notify the client."""

        return cls(data_point=payload["data_point"])

    @classmethod
    def notify_subs(cls, data_point: DataPoint):
        """Notify subscribers querying for the peripheral and data point type"""

        group = cls._get_peripheral_group(data_point)
        cls.broadcast_sync(group=group, payload={"data_point": data_point})
        group = cls._get_data_point_type_group(data_point)
        cls.broadcast_sync(group=group, payload={"data_point": data_point})

    @staticmethod
    def _get_peripheral_group(data_point: DataPoint) -> str:
        return f"data_point:{data_point.peripheral_component_id}"

    @staticmethod
    def _get_data_point_type_group(data_point: DataPoint) -> str:
        return f"data_point:{data_point.data_point_type_id}"

    @staticmethod
    def _to_data_point_group(uuid: str) -> str:
        return f"data_point:{uuid}"


class ControllerMessageSubscription(Subscription):
    """GraphQL subscription for controller messages."""

    controller_message = graphene.Field(ControllerMessageNode)

    class Arguments:
        """Specify a list of controllers."""

        controller_ids = graphene.List(graphene.ID, required=True)

    @classmethod
    def subscribe(cls, root, info, controller_ids):
        topics = [cls._to_group(from_global_id(i)[1]) for i in controller_ids]
        if topics:
            return topics
        return None

    @classmethod
    def publish(cls, payload, info, **kwargs):
        """Sends a new controller message to the client."""

        return cls(controller_message=payload["controller_message"])

    @classmethod
    def notify_subs(cls, controller_message: ControllerMessage):
        """Notify subscribers querying for messages from a controller."""

        group = cls._get_controller_group(controller_message)
        cls.broadcast_sync(
            group=group, payload={"controller_message": controller_message}
        )

    @staticmethod
    def _get_controller_group(controller_message: ControllerMessage) -> str:
        return f"controller_message:{controller_message.controller_id}"

    @staticmethod
    def _to_group(uuid: str) -> str:
        return f"controller_message:{uuid}"
