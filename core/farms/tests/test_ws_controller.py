from asgiref.sync import sync_to_async
import uuid

from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, AsyncClient
from django.urls import reverse
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from core.routing import application
from farms.models import (
    Site,
    SiteEntity,
    ControllerComponentType,
    ControllerComponent,
    ControllerMessage,
    ControllerAuthToken,
    ControllerTask,
    PeripheralComponent,
)


class TestControllerMessage(TransactionTestCase):
    """Test the websockets Controller messages API"""

    @staticmethod
    def init_db():
        """Seed database for WS controller tests"""
        user = get_user_model().objects.create_user("user_a@example.com", "passwd_a")
        site = Site.objects.create(name="Site A", owner=user)
        controller_entity = SiteEntity.objects.create(name="ESP32 - A", site=site)
        esp32 = ControllerComponentType.objects.create(name="ESP32")
        controller_component = ControllerComponent.objects.create(
            site_entity=controller_entity, component_type=esp32
        )
        ControllerAuthToken.objects.create(controller=controller_component)
        return controller_entity

    def setUp(self):
        self.ws_url = "ws-api/v1/farms/controllers/"
        self.controller_entity = self.init_db()
        self.auth_token = (
            f"token_{self.controller_entity.controller_component.auth_token.key}"
        )

    async def test_authentication(self):
        """Test that only connections from authenticated controllers are accepted"""

        valid_auth_token = self.auth_token
        invalid_auth_token = self.auth_token + "XYZ"

        # Connect as anonymous controller
        communicator = WebsocketCommunicator(
            application,
            self.ws_url,
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

        # Connect as registered user
        communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[valid_auth_token],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

        # Connect with invalid token
        communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[invalid_auth_token],
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

        # Close communicator
        await communicator.disconnect()

    async def test_sending_malformed_json(self):
        """Test that the messages are validated"""

        # Connect...
        communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[self.auth_token],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # ... and send malformed JSON...
        data = "This is not JSON"
        await communicator.send_to(data)
        response = await communicator.receive_json_from()
        self.assertIn("errors", response)

        # ... and expect to be disconnected
        output = await communicator.receive_output()
        self.assertEqual("websocket.close", output["type"])

        await communicator.disconnect()

    async def test_sending_without_type_in_json(self):
        """Test that the messages are validated"""

        # Connect...
        communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[self.auth_token],
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

    async def test_sending_valid_message(self):
        """Test that the messages are validated"""

        # Connect...
        communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[self.auth_token],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # ... and send proper JSON...
        data = {"type": ControllerMessage.ERROR_TYPE, "errors": "The Error Details"}
        await communicator.send_json_to(data)
        self.assertTrue(await communicator.receive_nothing())

        # ... and expect it to be saved
        saved_message = await database_sync_to_async(ControllerMessage.objects.first)()
        self.assertDictEqual(data, saved_message.message)

        await communicator.disconnect()

    async def test_multiple_connections(self):
        """Test that not more than one WS connection exists per controller"""

        # Connect...
        first_communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[self.auth_token],
        )
        connected, _ = await first_communicator.connect()
        self.assertTrue(connected)

        # Connect...
        second_communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[self.auth_token],
        )
        connected, _ = await second_communicator.connect()
        self.assertTrue(connected)

        # ... and expect the second one to receive the data
        data = {"type": ControllerMessage.ERROR_TYPE, "error": "some error"}
        await second_communicator.send_json_to(data)
        self.assertTrue(await second_communicator.receive_nothing())

        # ... and expect it to be saved
        saved_message = await database_sync_to_async(ControllerMessage.objects.first)()
        self.assertDictEqual(data, saved_message.message)

        await first_communicator.disconnect()
        await second_communicator.disconnect()

    # async def test_rest_api_to_ws_connection(self):
    #     """Test that the messages are validated"""

    #     client = Client()

    #     # Connect...
    #     communicator = WebsocketCommunicator(
    #         application,
    #         self.ws_url,
    #         subprotocols=[self.auth_token],
    #     )
    #     connected, _ = await communicator.connect()
    #     self.assertTrue(connected)

    #     # Log in and send command over REST API
    #     logged_in = await sync_to_async(client.login)(
    #         username="user_a@example.com", password="passwd_a"
    #     )
    #     self.assertTrue(logged_in)
    #     data = {
    #         "type": ControllerMessage.COMMAND_TYPE,
    #         "peripheral": {
    #             "add": [
    #                 {
    #                     "uuid": str(uuid.uuid4()),
    #                     "name": "led33",
    #                     "type": PeripheralComponent.LED_TYPE,
    #                     "pin": 33,
    #                 }
    #             ]
    #         },
    #         "task": {
    #             "create": [
    #                 {
    #                     "uuid": str(uuid.uuid4()),
    #                     "type": ControllerTask.TaskType.READ_SENSOR,
    #                 }
    #             ]
    #         },
    #     }
    #     response = await database_sync_to_async(client.post)(
    #         reverse("controller-command", kwargs={"pk": self.controller_entity.pk}),
    #         data=data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 200)

    #     # Check that data was received
    #     received_data = await communicator.receive_json_from()
    #     command = data["peripheral"]["add"][0]
    #     self.assertIn(command["uuid"], str(received_data))
    #     self.assertIn(command["type"], str(received_data))
    #     self.assertIn(str(command["pin"]), str(received_data))
    #     await communicator.disconnect()

    # def test_rest_api_error_handling(self):
    #     """Test the error handling for invalid input"""

    #     # Check authentication requirement
    #     client = Client()
    #     response = client.post(
    #         reverse("controller-command", kwargs={"pk": uuid.uuid4()}),
    #         data={},
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 401)

    #     # Check error for non-existant controller
    #     client.force_login(self.controller_entity.site.owner)
    #     response = client.post(
    #         reverse("controller-command", kwargs={"pk": uuid.uuid4()}),
    #         data={},
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 404)

    #     # Check error for unauthorized user
    #     user_b = get_user_model().objects.create_user("user_b@example.com", "passwd_b")
    #     client.force_login(user_b)
    #     response = client.post(
    #         reverse("controller-command", kwargs={"pk": self.controller_entity.id}),
    #         data={},
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 403)

    #     # Check that the channel has to be set
    #     client.force_login(self.controller_entity.site.owner)
    #     response = client.post(
    #         reverse("controller-command", kwargs={"pk": self.controller_entity.id}),
    #         data={},
    #         content_type="application/json",
    #     )
    #     self.assertContains(response, "channel not set", status_code=400)

    #     # Check sending an invalid message
    #     self.controller_entity.controller_component.channel_name = "some_channel"
    #     self.controller_entity.controller_component.save()
    #     response = client.post(
    #         reverse("controller-command", kwargs={"pk": self.controller_entity.id}),
    #         data={
    #             "type": "whatever",
    #         },
    #         content_type="application/json",
    #     )
    #     self.assertContains(response, "message type", status_code=400)

    #     response = client.post(
    #         reverse("controller-command", kwargs={"pk": self.controller_entity.id}),
    #         data={
    #             "type": ControllerMessage.COMMAND_TYPE,
    #             "peripheral": {"add": [{"not_uuid": "something something"}]},
    #         },
    #         content_type="application/json",
    #     )
    #     self.assertContains(response, "Missing key", status_code=400)

    async def test_result_message(self):
        """Test that the consumer handles result messages from the controller"""

        # Connect...
        communicator = WebsocketCommunicator(
            application,
            self.ws_url,
            subprotocols=[self.auth_token],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Set up peripherals
        peripheral_a_entity = await database_sync_to_async(SiteEntity.objects.create)(
            name="Peripheral A", site=self.controller_entity.site
        )
        peripheral_b_entity = await database_sync_to_async(SiteEntity.objects.create)(
            name="Peripheral B", site=self.controller_entity.site
        )
        peripheral_a = await database_sync_to_async(PeripheralComponent.objects.create)(
            site_entity=peripheral_a_entity,
            peripheral_type=PeripheralComponent.PeripheralType.PWM,
            controller_component=self.controller_entity.controller_component,
            state=PeripheralComponent.State.ADDING,
        )
        peripheral_b = await database_sync_to_async(PeripheralComponent.objects.create)(
            site_entity=peripheral_b_entity,
            peripheral_type=PeripheralComponent.PeripheralType.PWM,
            controller_component=self.controller_entity.controller_component,
            state=PeripheralComponent.State.REMOVING,
        )
        # Set up tasks
        task_a = await database_sync_to_async(ControllerTask.objects.create)(
            task_type=ControllerTask.TaskType.READ_SENSOR,
            controller_component=self.controller_entity.controller_component,
            state=ControllerTask.State.STARTING,
            parameters={},
        )
        task_b = await database_sync_to_async(ControllerTask.objects.create)(
            task_type=ControllerTask.TaskType.READ_SENSOR,
            controller_component=self.controller_entity.controller_component,
            state=ControllerTask.State.STOPPING,
            parameters={},
        )

        # Send successful and and remove result message
        data = {
            "type": "result",
            "request_id": "some_request",
            "peripheral": {
                "add": [{"uuid": str(peripheral_a.pk), "status": "success"}],
                "remove": [{"uuid": str(peripheral_b.pk), "status": "success"}],
            },
            "task": {
                "start": [{"uuid": str(task_a.pk), "status": "success"}],
                "stop": [{"uuid": str(task_b.pk), "status": "success"}],
            },
        }
        await communicator.send_json_to(data)
        self.assertTrue(await communicator.receive_nothing())

        # Expect both peripherals and tasks to be in new states
        peripheral_a = await database_sync_to_async(PeripheralComponent.objects.get)(
            pk=peripheral_a.pk
        )
        self.assertEqual(peripheral_a.state, PeripheralComponent.State.ADDED)

        peripheral_b = await database_sync_to_async(PeripheralComponent.objects.get)(
            pk=peripheral_b.pk
        )
        self.assertEqual(peripheral_b.state, PeripheralComponent.State.REMOVED)

        task_a = await database_sync_to_async(ControllerTask.objects.get)(pk=task_a.pk)
        self.assertEqual(task_a.state, ControllerTask.State.RUNNING)

        task_b = await database_sync_to_async(ControllerTask.objects.get)(pk=task_b.pk)
        self.assertEqual(task_b.state, ControllerTask.State.STOPPED)

        await communicator.disconnect()
