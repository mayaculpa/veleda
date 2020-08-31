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
from farms.models import Site, Controller, ControllerMessage, ControllerToken


@database_sync_to_async
def create_user(email, password):
    """Create a user in an async environment"""
    return get_user_model().objects.create_user(email, password)


@database_sync_to_async
def init_db():
    """Seed database for WS controller tests"""
    user = get_user_model().objects.create_user("user_a@example.com", "passwd_a")
    site = Site.objects.create(name="Site A", owner=user)
    controller = Controller.objects.create(
        site=site,
        name="Controller A",
        wifi_mac_address="AA:AA:AA:AA:AA:AA",
        external_ip_address="1.1.1.1",
    )
    ControllerToken.objects.create(controller=controller)
    return controller


class TestControllerMessage(TransactionTestCase):
    """Test the websockets Controller messages API"""

    def test_authentication(self):
        """Test that only connections from authenticated controllers are accepted"""

        async def test_body():
            controller = await init_db()

            # Connect as anonymous controller
            communicator = WebsocketCommunicator(
                application,
                "ws-api/v1/farms/controllers/",
            )
            connected, _ = await communicator.connect()
            self.assertFalse(connected)
            await communicator.disconnect()

            # Connect as registered user
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/controllers/",
                subprotocols=[f"token_{controller.auth_token.key}"],
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.disconnect()


            # Connect with invalid token
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/controllers/",
                subprotocols=[f"token_{controller.auth_token.key}XYZ"],
            )
            connected, _ = await communicator.connect()
            self.assertFalse(connected)

            # Close communicator
            await communicator.disconnect()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_body())
    
    def test_sending_malformed_json(self):
        """Test that the messages are validated"""

        async def test_body():
            controller = await init_db()

            # Connect...
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/controllers/",
                subprotocols=[f"token_{controller.auth_token.key}"],
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            # ... and send malformed JSON...
            data = "This is not JSON"
            await communicator.send_to(data)
            response = await communicator.receive_json_from()
            self.assertIn("error", response)

            # ... and expect to be disconnected
            output = await communicator.receive_output()
            self.assertEqual("websocket.close", output["type"])

            await communicator.disconnect()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_body())

    def test_sending_without_type_in_json(self):
        """Test that the messages are validated"""

        async def test_body():
            controller = await init_db()

            # Connect...
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/controllers/",
                subprotocols=[f"token_{controller.auth_token.key}"],
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            # ... and send malformed JSON...
            data = {"hello": "there"}
            await communicator.send_json_to(data)
            response = await communicator.receive_json_from()
            self.assertIn("errors", response)

            # ... and expect to be disconnected
            output = await communicator.receive_output()
            self.assertEqual("websocket.close", output["type"])

            await communicator.disconnect()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_body())

    def test_sending_valid_message(self):
        """Test that the messages are validated"""

        async def test_body():
            controller = await init_db()

            # Connect...
            communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/controllers/",
                subprotocols=[f"token_{controller.auth_token.key}"],
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            # ... and send proper JSON...
            data = {"type": "tel", "number": 12}
            await communicator.send_json_to(data)

            self.assertTrue(await communicator.receive_nothing())
            
            # ... and expect it to be saved
            saved_message = await database_sync_to_async(ControllerMessage.objects.first)()
            self.assertDictEqual(data, saved_message.message)

            await communicator.disconnect()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_body())
    
    def test_multiple_connections(self):
        """Test that the messages are validated"""

        async def test_body():
            controller = await init_db()

            # Connect...
            first_communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/controllers/",
                subprotocols=[f"token_{controller.auth_token.key}"],
            )
            connected, _ = await first_communicator.connect()
            self.assertTrue(connected)

            # Connect...
            second_communicator = WebsocketCommunicator(
                application, f"ws-api/v1/farms/controllers/",
                subprotocols=[f"token_{controller.auth_token.key}"],
            )
            connected, _ = await second_communicator.connect()
            self.assertTrue(connected)

            # ... and expect the first one to be disconnected
            output = await first_communicator.receive_output()
            self.assertEqual("websocket.close", output["type"])

            await first_communicator.disconnect()

            # ... and send proper JSON...
            data = {"type": "tel", "number": 99}
            await second_communicator.send_json_to(data)

            self.assertTrue(await second_communicator.receive_nothing())
            
            # ... and expect it to be saved
            saved_message = await database_sync_to_async(ControllerMessage.objects.first)()
            self.assertDictEqual(data, saved_message.message)

            await second_communicator.disconnect()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_body())