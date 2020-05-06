# import pytest
import asyncio
import datetime
import json

from channels.testing import ChannelsLiveServerTestCase
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, TestCase
from django.urls import reverse
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
import pytz

from core.routing import application
from farms.models import Site, Coordinator, MqttMessage
from farms.serializers import WsMqttMessageSerializer


# @database_sync_to_async
# def create_user(email, password):
#     """Create a user in an async environment"""
#     return get_user_model().objects.create_user(email, password)


# @pytest.mark.asyncio
# @pytest.mark.django_db(transaction=True)
# class TestMqttMessages:
#     """Test the websocket MQTT messages API"""

#     async def test_authorized_user_can_connect(self):
#         """Test the authorization"""
#         client = Client()
#         user = await create_user("user_a@example.com", "passwd_a")
#         logged_in = await client.login(email=user.email, password="passwd_a")
#         assert logged_in is True

#         communicator = WebsocketCommunicator(
#             application=application,
#             path=reverse("ws-mqtt-messages"),
#             headers=[(
#                 b"cookie",
#                 f"sessionid={client.cookies['sessionid'].value}".encode("ascii")
#             )]
#         )
#         connected, _ = await communicator.connect()
#         assert connected is False
#         await communicator.disconnect()


@database_sync_to_async
def init_db():
    """Seed database for WS tests"""
    # import ipdb; ipdb.set_trace()
    user = get_user_model().objects.create_user("user_a@example.com", "passwd_a")
    site = Site.objects.create(name="Site A", owner=user)
    coordinator = Coordinator.objects.create(
        site=site, local_ip_address="10.0.0.2", external_ip_address="1.1.1.1",
    )
    return user, site, coordinator

class TestMqttMessages(TransactionTestCase):
    """Test the websockets MQTT messages API"""

    def test_authentication(self):
        """Test that only connections from authenticated users are accepted"""

        async def test_body():
            user, _, coordinator = await init_db()

            # Connect as anonymous user
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/coordinators/{coordinator.id}/",
            )
            connected, _ = await communicator.connect()
            self.assertFalse(connected)
            await communicator.disconnect()

            # Connect as registered user
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/coordinators/{coordinator.id}/",
            )
            communicator.scope["user"] = user
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.disconnect()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_body())

    def test_writing_to_api(self):
        """Test sending MQTT messages as a coordinator to the server"""

        async def test_body():
            user, _, coordinator = await init_db()

            # Connect as a registered user
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/coordinators/{coordinator.id}/"
            )
            communicator.scope["user"] = user
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            # Create a serialized MQTT message and send it
            message = {"some": "json", "status": "ok"}
            now = pytz.utc.localize(datetime.datetime.utcnow())
            data = {
                "type": "mqtt-message",
                "created_at": now.isoformat(),
                "coordinator": str(coordinator.id),
                "message": message,
                "topic_prefix": MqttMessage.REGISTER_PREFIX,
            }
            self.assertTrue(await communicator.receive_nothing())

            # Expect missing fields to cause the connection to be closed
            data = {
                "type": "hello world",
            }
            await communicator.send_json_to(data)
            response = await communicator.receive_json_from()
            self.assertIn("error", response)

            # Send malformed JSON and expect to be disconnected
            data = "This is not JSON"
            await communicator.send_to(data)
            response = await communicator.receive_json_from()
            self.assertIn("error", response)

            # Check that the websocket is closed
            await communicator.send_to(data)
            output = await communicator.receive_output()
            self.assertEqual("websocket.close", output["type"])
            
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_body())
