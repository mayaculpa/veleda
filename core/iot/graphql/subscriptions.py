import channels_graphql_ws
import graphene
from graphql_relay import from_global_id

from iot.models import DataPoint
from iot.graphql.nodes import DataPointNode


class DataPointSubscription(channels_graphql_ws.Subscription):
    """Simple GraphQL subscription."""

    data_point = graphene.Field(DataPointNode)

    class Arguments:
        """That is how subscription arguments are defined."""

        peripheral_ids = graphene.List(graphene.ID, required=False)
        data_point_type_ids = graphene.List(graphene.ID, required=False)

    @staticmethod
    def subscribe(root, info, **kwargs):
        """Called when user subscribes."""

        topics = []

        if peripheral_ids := kwargs.get("peripheral_ids"):
            topics.extend(
                [
                    DataPointSubscription._to_data_point_group(from_global_id(i)[1])
                    for i in peripheral_ids
                ]
            )
        if data_point_type_ids := kwargs.get("data_point_type_ids"):
            topics.extend(
                [
                    DataPointSubscription._to_data_point_group(from_global_id(i)[1])
                    for i in data_point_type_ids
                ]
            )

        if topics:
            return topics
        return None

    @staticmethod
    def publish(payload, info, **kwargs):
        """Called to notify the client."""

        return DataPointSubscription(data_point=payload["data_point"])

    @classmethod
    def new_data_point(cls, data_point):
        """Notify subscribers querying for the peripheral and data point type"""

        group = cls._get_peripheral_group(data_point)
        DataPointSubscription.broadcast_sync(
            group=group, payload={"data_point": data_point}
        )
        group = cls._get_data_point_type_group(data_point)
        DataPointSubscription.broadcast_sync(
            group=group, payload={"data_point": data_point}
        )

    @staticmethod
    def _get_peripheral_group(data_point: DataPoint) -> str:
        return f"data_point:{data_point.peripheral_component_id}"

    @staticmethod
    def _get_data_point_type_group(data_point: DataPoint) -> str:
        return f"data_point:{data_point.data_point_type_id}"

    @staticmethod
    def _to_data_point_group(uuid: str) -> str:
        return f"data_point:{uuid}"
