from datetime import datetime, timedelta
import json
import logging
import pytz
from unittest import mock
import uuid

from address.models import Address
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Farm, Coordinator, HydroponicSystem, Controller
from accounts.models import Profile

# from core.celery import debug_task


class FarmTests(TestCase):
    def test_farm_components(self):
        """Test creating a farm and its components."""

        proto_farm_owner = get_user_model().objects.create_user(
            email="owner@example.com", password="owners_passwd",
        )
        proto_farm_owner.profile.short_name = "Dude"
        proto_farm_owner.profile.full_name = "Dr. Owner C. Dude"
        proto_farm_owner.save()

        proto_farm_address = Address.objects.create(
            raw="Some Street 42, Any Town, Major City, New Country",
        )
        farm = Farm.objects.create(
            name="ProtoFarm", owner=proto_farm_owner, address=proto_farm_address
        )
        self.assertEqual(
            farm.owner.profile.short_name, proto_farm_owner.profile.short_name
        )
        self.assertEqual(farm.address.raw, proto_farm_address.raw)

        coordinator = Coordinator.objects.create(
            farm=farm, local_ip_address="192.168.0.2", external_ip_address="1.1.1.1"
        )
        hydroponic_system_a = HydroponicSystem.objects.create(farm=farm,)
        hydroponic_system_b = HydroponicSystem.objects.create(farm=farm,)
        controller_a = Controller.objects.create(
            farm=farm,
            controller_type=Controller.SENSOR_CONTROLLER,
            wifi_mac_address="00:11:22:33:44:55",
        )
        controller_b = Controller.objects.create(
            farm=farm,
            controller_type=Controller.PUMP_CONTROLLER,
            wifi_mac_address="00:11:22:33:44:56",
        )
        self.assertEqual(farm.coordinator.id, coordinator.id)
        self.assertEqual(controller_a.farm.id, farm.id)
        self.assertEqual(controller_b.farm.id, farm.id)
        self.assertEqual(hydroponic_system_a.farm.id, farm.id)
        self.assertEqual(hydroponic_system_b.farm.id, farm.id)

    def test_farm_timestamps(self):
        """Test creating a farm and check that the timestamps update correctly"""

        mocked_now = datetime.now(pytz.utc)
        with mock.patch("django.utils.timezone.now", return_value=mocked_now):
            farm = Farm.objects.create(name="ProtoFarm")
            coordinator = Coordinator.objects.create(
                farm=farm, local_ip_address="192.168.0.2", external_ip_address="1.1.1.1"
            )
            hydroponic_system = HydroponicSystem.objects.create(
                farm=farm, system_type=HydroponicSystem.FLOOD_AND_DRAIN
            )
            controller = Controller.objects.create(
                farm=farm,
                controller_type=Controller.SENSOR_CONTROLLER,
                wifi_mac_address="00:11:22:33:44:55",
            )

        self.assertEqual(farm.created_at, mocked_now)
        self.assertEqual(farm.modified_at, mocked_now)
        self.assertEqual(coordinator.created_at, mocked_now)
        self.assertEqual(coordinator.modified_at, mocked_now)
        self.assertEqual(hydroponic_system.created_at, mocked_now)
        self.assertEqual(hydroponic_system.modified_at, mocked_now)
        self.assertEqual(controller.created_at, mocked_now)
        self.assertEqual(controller.modified_at, mocked_now)

        mocked_later = mocked_now + timedelta(hours=1)
        with mock.patch("django.utils.timezone.now", return_value=mocked_later):
            farm.name = "New name"
            farm.save()
            coordinator.local_ip_address = "192.168.0.2"
            coordinator.save()
            hydroponic_system.name = "A Flood and drain system"
            hydroponic_system.save()
            controller.wifi_mac_address = "11:22:33:44:55:66"
            controller.save()

        self.assertEqual(farm.created_at, mocked_now)
        self.assertEqual(farm.modified_at, mocked_later)
        self.assertEqual(coordinator.created_at, mocked_now)
        self.assertEqual(coordinator.modified_at, mocked_later)
        self.assertEqual(hydroponic_system.created_at, mocked_now)
        self.assertEqual(hydroponic_system.modified_at, mocked_later)
        self.assertEqual(controller.created_at, mocked_now)
        self.assertEqual(controller.modified_at, mocked_later)

    def test_controller_registration_flow(self):
        """Test a new controller automatically registering itself and being assigned to a farm."""

        farm = Farm.objects.create(name="ProtoFarm")
        coordinator = Coordinator.objects.create(
            farm=farm, local_ip_address="192.168.0.2", external_ip_address="3.3.3.3"
        )
        controller_a = Controller.objects.create(
            wifi_mac_address="00:11:22:33:44:55", external_ip_address="3.3.3.3"
        )
        controller_b = Controller.objects.create(
            wifi_mac_address="00:11:22:33:44:56", external_ip_address="3.3.3.3"
        )

        unregistered_controllers = Controller.objects.get_local_unregistered_controllers(
            coordinator.external_ip_address
        )
        self.assertIn(controller_a, unregistered_controllers)
        self.assertIn(controller_b, unregistered_controllers)

        controller_a.farm = farm
        controller_a.save()
        updated_unregistered_controllers = Controller.objects.get_local_unregistered_controllers(
            coordinator.external_ip_address
        )
        self.assertNotIn(controller_a, updated_unregistered_controllers)


class CoordinatorSetupTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_coordinator_setup(self):
        """Test that pinging coordinators can be found"""

        # Test internal IP address
        response = self.client.get(reverse("coordinator_setup"), REMOTE_ADDR="127.0.0.1")
        self.assertContains(response, "external IP address can not be used for a lookup")
        self.assertContains(response, "127.0.0.1")

        # Test empty setup page
        response = self.client.get(reverse("coordinator_setup"), REMOTE_ADDR="1.1.1.1")
        self.assertContains(response, "no coordinators were found")

        # Test only registered coordinators
        farm_a_1 = Farm.objects.create(name="TestFarm_A_1")
        farm_a_2 = Farm.objects.create(name="TestFarm_A_2")
        coordinator_a_1 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1", farm=farm_a_1
        )
        coordinator_a_2 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1", farm=farm_a_2
        )
        response = self.client.get(reverse("coordinator_setup"), REMOTE_ADDR="1.1.1.1")
        self.assertContains(response, coordinator_a_1.farm.name)
        self.assertContains(response, coordinator_a_2.farm.name)
        self.assertContains(response, "None found")

        coordinator_b_1 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        coordinator_b_2 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        response = self.client.get(reverse("coordinator_setup"), REMOTE_ADDR="1.1.1.1")
        self.assertContains(response, coordinator_b_1.id.hex[:7])
        self.assertContains(response, coordinator_b_2.id.hex[:7])

        response = self.client.get(reverse("coordinator_setup"), REMOTE_ADDR="1.1.1.2")
        self.assertContains(response, "no coordinators were found")

class CoordinatorAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        # Disable HTTP request warnings
        logging.disable()

    def tearDown(self):
        # Reenable HTTP request warnings
        logging.disable(logging.NOTSET)

    def test_controller_ping(self):
        """Test unregistered coordinators pinging the server"""

        # Test passing an empty POST request
        data = {}
        response = self.client.post(
            reverse("coordiantor_ping"), data=data, REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "This field is required", status_code=400)

        # Test passing invalid JSON
        data = "{hello there}"
        response = self.client.post(
            reverse("coordiantor_ping"),
            data=data,
            content_type="application/json",
            REMOTE_ADDR="1.1.1.1",
        )
        self.assertContains(response, "JSON parse error", status_code=400)

        # Test passing 127.0.0.1 as the remote IP address. Should fail as not routable
        data = {"local_ip_address": "192.168.0.2"}
        response = self.client.post(reverse("coordiantor_ping"), data=data)
        self.assertContains(response, "IP address is not routable", status_code=400)

        # Test a valid ping
        data = {"local_ip_address": "192.168.0.2"}
        response = self.client.post(
            reverse("coordiantor_ping"), data=data, REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "local_ip_address", status_code=201)
        self.assertContains(response, "external_ip_address", status_code=201)
        self.assertContains(response, "id", status_code=201)

        # Test another anonymous valid ping
        data = {"local_ip_address": "192.168.0.2"}
        response = self.client.post(
            reverse("coordiantor_ping"), data=data, REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "local_ip_address", status_code=201)
        self.assertContains(response, "external_ip_address", status_code=201)
        self.assertContains(response, "id", status_code=201)

        # Test a valid ping from a known coordinator
        data = {
            "local_ip_address": "192.168.0.2",
            id: json.loads(response.content)["id"],
        }
        response = self.client.post(
            reverse("coordiantor_ping"), data=data, REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "local_ip_address", status_code=201)
        self.assertContains(response, "external_ip_address", status_code=201)
        self.assertContains(response, "id", status_code=201)

        # Register the coordinator and send an invalid ping. Expect the response to
        # contain the correct URL (consists of the coordinator-detail view + id)
        farm = Farm.objects.create(name="TestFarm")
        coordinator = Coordinator.objects.create(
            farm=farm, local_ip_address="192.168.0.1", external_ip_address="1.1.1.3"
        )
        data = {"local_ip_address": "192.168.0.2", "id": coordinator.id}
        response = self.client.post(
            reverse("coordiantor_ping"), data=data, REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "has been registered", status_code=403)
        self.assertContains(response, coordinator.id, status_code=403)


# class FlowTests(TestCase):
#     def setUp(self):
#         self.client = Client()

#     def test_coordinator_registration_flow(self):
#         """
#         Test a coordinator pinging the server, being added by a user, updating the dns
#         records and requesting new TLS certificates.
#         """


#     def test_celery(self):
#         debug_task.delay()
