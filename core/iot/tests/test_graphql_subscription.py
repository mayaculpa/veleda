import warnings

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from graphql_relay.node.node import to_global_id

from core.routing import application
from iot.models import (
    ControllerComponent,
    ControllerComponentType,
    DataPoint,
    DataPointType,
    PeripheralComponent,
    Site,
    SiteEntity,
)
from iot.models.controller import ControllerMessage


def catch_warnings(func):
    """Catch specific GraphQL consumer warnings due to testing env."""

    def wrapper(self):
        with warnings.catch_warnings(record=True) as warning_messages:
            warnings.filterwarnings(
                "ignore", message="async_to_sync was passed a non-async-marked callable"
            )
            func(self)
            for message in warning_messages:
                print(message.message)

    return wrapper


class TestGraphQLSubscription(TransactionTestCase):
    """Test GraphQL subscriptions."""

    def setUp(self):
        self.ws_url = "graphql/"
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self.owner_z = get_user_model().objects.create_user(
            email="ownerB@bar.com", password="foo"
        )
        self.site_a = Site.objects.create(name="Site A", owner=self.owner_a)
        self.site_z = Site.objects.create(name="Site Z", owner=self.owner_z)
        self.esp32_type = ControllerComponentType.objects.create(name="ESP32")
        self.controller_a = ControllerComponent.objects.create(
            component_type=self.esp32_type,
            site_entity=SiteEntity.objects.create(name="SomeESP32", site=self.site_a),
        )
        self.controller_z = ControllerComponent.objects.create(
            component_type=self.controller_a.component_type,
            site_entity=SiteEntity.objects.create(name="AnyESP32", site=self.site_z),
        )
        self.peripheral_a = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.ANALOG_IN,
            site_entity=SiteEntity.objects.create(name="PeriA", site=self.site_a),
            controller_component=self.controller_a,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.peripheral_z = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.DIGITAL_IN,
            site_entity=SiteEntity.objects.create(name="PeriZ", site=self.site_z),
            controller_component=self.controller_z,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.data_point_type_a = DataPointType.objects.create(name="dptA", unit="uA")
        self.data_point_type_z = DataPointType.objects.create(
            name="dptZ", unit="uZ", created_by=self.owner_z
        )

    async def open_graphql_session(self) -> WebsocketCommunicator:
        communicator = WebsocketCommunicator(
            application, self.ws_url, subprotocols=["graphql-ws"]
        )
        communicator.scope["user"] = self.owner_a
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({"type": "connection_init", "payload": {}})
        await communicator.receive_nothing()
        return communicator

    async def test_authentication(self):
        """Test that only logged in users are accepted."""

        communicator = WebsocketCommunicator(
            application, self.ws_url, subprotocols=["graphql-ws"]
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

        communicator = WebsocketCommunicator(
            application, self.ws_url, subprotocols=["graphql-ws"]
        )
        communicator.scope["user"] = self.owner_a
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

    @catch_warnings
    @async_to_sync
    async def test_data_point_sub_1(self):
        """Test creating a subscription and receiving data"""
        communicator = await self.open_graphql_session()
        peripheral_gid = to_global_id("PeripheralComponentNode", self.peripheral_a.pk)
        subscription = {
            "id": "1",
            "type": "start",
            "payload": {
                "query": f"""
                    subscription s {{
                      dataPointSubscription(peripheralIds: "{peripheral_gid}") {{
                        dataPoint {{
                          time, value, dataPointType {{ name }}
                        }}
                      }}
                    }}
                """,
                "variables": None,
                "operationName": "s",
            },
        }
        await communicator.send_json_to(subscription)
        output = await communicator.receive_json_from()
        self.assertDictEqual({"type": "connection_ack"}, output)
        data_point = await database_sync_to_async(DataPoint.objects.create)(
            value=56.8,
            peripheral_component=self.peripheral_a,
            data_point_type=self.data_point_type_a,
        )
        output = await communicator.receive_json_from()
        self.assertEqual(
            data_point.value,
            output["payload"]["data"]["dataPointSubscription"]["dataPoint"]["value"],
        )

    @catch_warnings
    @async_to_sync
    async def test_data_point_sub_2(self):
        """Test creating a subscription and receiving data"""
        communicator = await self.open_graphql_session()
        data_point_type_gid = to_global_id(
            "PeripheralComponentNode", self.data_point_type_a.pk
        )
        subscription = {
            "id": "1",
            "type": "start",
            "payload": {
                "query": f"""
                    subscription s {{
                      dataPointSubscription(peripheralIds: ["{data_point_type_gid}"]) {{
                        dataPoint {{
                          time, value, dataPointType {{ name }}
                        }}
                      }}
                    }}
                """,
                "variables": None,
                "operationName": "s",
            },
        }
        await communicator.send_json_to(subscription)
        output = await communicator.receive_json_from()
        self.assertDictEqual({"type": "connection_ack"}, output)
        data_point = await database_sync_to_async(DataPoint.objects.create)(
            value=56.8,
            peripheral_component=self.peripheral_a,
            data_point_type=self.data_point_type_a,
        )
        output = await communicator.receive_json_from()
        self.assertEqual(
            data_point.value,
            output["payload"]["data"]["dataPointSubscription"]["dataPoint"]["value"],
        )

    @catch_warnings
    @async_to_sync
    async def test_controller_message_subscription(self):
        """Test subscribing to controller messages"""
        communicator = await self.open_graphql_session()
        controller_gid = to_global_id("ControllerComponentNode", self.controller_a.pk)
        subscription = {
            "id": "1",
            "type": "start",
            "payload": {
                "query": f"""
                    subscription s {{
                      controllerMessageSubscription(controllerIds: ["{controller_gid}"]) {{
                        controllerMessage {{
                          createdAt, controller {{ id }}, message, messageType, requestId
                        }}
                      }}
                    }}
                """,
                "variables": None,
                "operationName": "s",
            },
        }
        await communicator.send_json_to(subscription)
        output = await communicator.receive_json_from()
        self.assertDictEqual({"type": "connection_ack"}, output)
        controller_message = await database_sync_to_async(
            ControllerMessage.objects.create
        )(
            controller=self.controller_a,
            message={"type": "sys"},
            request_id="asdölkj",
        )
        output = await communicator.receive_json_from()
        data = output["payload"]["data"]
        result = data["controllerMessageSubscription"]["controllerMessage"]
        self.assertEqual(controller_message.request_id, result["requestId"])
