from datetime import datetime, timedelta
import json
import logging
import pytz
from unittest import mock, skipIf
import uuid

from address.models import Address
import CloudFlare
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.test import Client, TestCase, tag
from django.urls import reverse

from accounts.models import Profile
from .models import Farm, Coordinator, HydroponicSystem, Controller
from .tasks import setup_subdomain_task


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
        self.user_a = get_user_model().objects.create_user(
            email="user_a@example.com", password="user_a",
        )
        # Disable HTTP request warnings
        logging.disable()

    def tearDown(self):
        # Reenable HTTP request warnings
        logging.disable(logging.NOTSET)

    def test_coordinator_selection(self):
        """Test that pinging coordinators can be found"""

        # Test login required
        response = self.client.get(
            reverse("coordinator-setup-select"), REMOTE_ADDR="127.0.0.1"
        )
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("coordinator-setup-select")
        )

        # Test with authenticated user for remaining asserts
        self.client.login(username=self.user_a.email, password="user_a")

        # Test internal IP address
        response = self.client.get(
            reverse("coordinator-setup-select"), REMOTE_ADDR="127.0.0.1"
        )
        self.assertContains(
            response, "external IP address can not be used for a lookup"
        )
        self.assertContains(response, "127.0.0.1")

        # Test empty setup page
        response = self.client.get(
            reverse("coordinator-setup-select"), REMOTE_ADDR="1.1.1.1"
        )
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
        response = self.client.get(
            reverse("coordinator-setup-select"), REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, coordinator_a_1.farm.name)
        self.assertContains(response, coordinator_a_2.farm.name)
        self.assertContains(response, "None found")

        # Test listing unregistered coordinators
        coordinator_b_1 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        coordinator_b_2 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        response = self.client.get(
            reverse("coordinator-setup-select"), REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, coordinator_b_1.id.hex[:7])
        self.assertContains(response, coordinator_b_2.id.hex[:7])

        # Test not showing coordinators for a user from a different subnet
        response = self.client.get(
            reverse("coordinator-setup-select"), REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "no coordinators were found")

    def test_select_to_register(self):
        """Test that selecting a coordinator redirects to its registration"""

        # Test login required
        response = self.client.post(
            reverse("coordinator-setup-select"), REMOTE_ADDR="127.0.0.1"
        )
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("coordinator-setup-select")
        )

        # Test with a logged in user and valid coordinator for the remaining asserts
        self.client.login(username=self.user_a.email, password="user_a")
        coordinator_a_1 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )

        # Test blank post request
        data = {}
        response = self.client.post(reverse("coordinator-setup-select"), data)
        self.assertContains(response, "This field is required", status_code=400)

        # Test invalid UUID
        data = {"coordinator_id": coordinator_a_1.id.hex[:-1]}
        # import ipdb; ipdb.set_trace()
        response = self.client.post(reverse("coordinator-setup-select"), data)
        self.assertContains(response, "Enter a valid UUID", status_code=400)

        # Test a valid request
        data = {"coordinator_id": coordinator_a_1.id}
        response = self.client.post(reverse("coordinator-setup-select"), data)
        self.assertRedirects(
            response,
            reverse("coordinator-setup-register", kwargs={"pk": coordinator_a_1.id,}),
        )

    def test_register_coordinator(self):
        """Test registering a coordinator"""

        # Test login required
        coordinator_a = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        response = self.client.get(
            reverse("coordinator-setup-register", kwargs={"pk": coordinator_a.id}),
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertRedirects(
            response,
            reverse("login")
            + "?next="
            + reverse("coordinator-setup-register", kwargs={"pk": coordinator_a.id}),
        )

        # Test if the form fields were loaded
        response = self.client.get(
            reverse("coordinator-setup-register", kwargs={"pk": coordinator_a.id}),
            REMOTE_ADDR="127.0.0.1",
        )


class FarmTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = get_user_model().objects.create_user(
            email="user_a@example.com", password="user_a",
        )
        self.user_b = get_user_model().objects.create_user(
            email="user_b@example.com", password="user_b",
        )
        # Disable HTTP request warnings
        logging.disable()

    def tearDown(self):
        # Reenable HTTP request warnings
        logging.disable(logging.NOTSET)

    def test_create_farm(self):
        """Test creating a farm"""

        # Check required authentication
        response = self.client.get(reverse("farm-setup"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("farm-setup")
        )
        response = self.client.post(reverse("farm-setup"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("farm-setup")
        )

        with self.settings(
            STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
        ):
            self.client.login(username=self.user_a.email, password="user_a")
            response = self.client.get(reverse("farm-setup"))
            self.assertContains(response, "Name")
            self.assertContains(response, "Address")

            # Check poorly formatted requests
            data = {}
            response = self.client.post(reverse("farm-setup"), data)
            self.assertContains(response, "Farm Setup", status_code=400)

            data = {"name": "test farm"}
            response = self.client.post(reverse("farm-setup"), data)
            self.assertContains(response, "Farm Setup", status_code=400)

            data = {"address": "some place"}
            response = self.client.post(reverse("farm-setup"), data)
            self.assertContains(response, "Farm Setup", status_code=400)
            self.assertFalse(Farm.objects.all())

            # Check valid requests
            data = {"name": "good farm", "address": "some place"}
            response = self.client.post(reverse("farm-setup"), data)
            self.assertRedirects(response, reverse("farm-list"))
            self.assertTrue(Farm.objects.all())

            farm = Farm.objects.get(name=data["name"])
            self.assertEqual(farm.name, data["name"])
            self.assertEqual(farm.owner, self.user_a)

    def test_farm_list(self):
        """Test showing all farms registered to a user"""
        farm_address_a = Address.objects.create(
            raw="Some Street 42, Any Town, Major City, New Country",
        )
        farm_coordinator_a = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        farm_a = Farm.objects.create(
            name="Farm A", address=farm_address_a, coordinator=farm_coordinator_a
        )
        farm_b = Farm.objects.create(name="Farm B")

        # Test required authentication
        response = self.client.get(reverse("farm-list"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("farm-list")
        )

        # Test no owned farms
        self.client.login(username=self.user_a.email, password="user_a")
        response = self.client.get(reverse("farm-list"))
        self.assertContains(response, "Farms")
        self.assertContains(response, "No farms found")

        # Test one ownder farm
        farm_a.owner = self.user_a
        farm_a.save()
        farm_b.owner = self.user_b
        farm_b.save()
        response = self.client.get(reverse("farm-list"))
        self.assertContains(response, farm_a.name)
        self.assertNotContains(response, farm_b.name)
        self.assertContains(response, farm_address_a.raw)


@tag("external-api")
@skipIf(
    not settings.CLOUDFLARE_API_KEY
    or not settings.FARMS_SUBDOMAIN_NAMESPACE
    or not settings.SERVER_DOMAIN,
    "Missing settings (API key or dns config)",
)
class FarmTaskTests(TestCase):
    def setUp(self):
        self.cf = CloudFlare.CloudFlare(token=settings.CLOUDFLARE_API_KEY)
        self.subdomain = (
            "test_a."
            + settings.FARMS_SUBDOMAIN_NAMESPACE
            + "."
            + settings.SERVER_DOMAIN
        )
        self.zone = self.cf.zones.get(params={"name": settings.SERVER_DOMAIN})[0]

        # Disable HTTP request warnings
        logging.disable()

    def tearDown(self):
        try:
            dns_records = self.cf.zones.dns_records.get(
                self.zone["id"], params={"name": self.subdomain}
            )
            if dns_records:
                self.cf.zones.dns_records.delete(self.zone["id"], dns_records[0]["id"])
        except CloudFlareError as err:
            logger.warn(
                "Calling Cloudflare API failed: {} {}".format(int(err), str(err))
            )

        # Reenable HTTP request warnings
        logging.disable(logging.NOTSET)

    def test_setup_subdomain(self):
        """
        Expect the setup_subdomain task to create the subdomain, the OAuth2 credentials
        and start the Let's Encrypt certification process.
        """
        # As the test calls external APIs, ensure settings are set to testing values
        self.assertTrue(settings.TESTING)
        self.assertTrue(self.zone["id"])

        # Tests the validation checks needed to create a subdomain and certs
        farm = Farm.objects.create(name="Test Farm A")
        task = setup_subdomain_task.s(farm.id).apply()
        self.assertTrue(task.failed())
        self.assertIsInstance(task.result, ValidationError)

        farm.subdomain = self.subdomain
        farm.save()
        task = setup_subdomain_task.s(farm.id).apply()
        self.assertTrue(task.failed())
        self.assertIsInstance(task.result, ObjectDoesNotExist)

        coordinator = Coordinator.objects.create(
            local_ip_address="127.0.0.1", external_ip_address="1.1.1.1", farm=farm
        )
        task = setup_subdomain_task.s(farm.id).apply()
        self.assertEqual(task.status, "SUCCESS")

        # Verification
        # Check that the farm subdomain has been created. Tear down will delete it
        # import ipdb; ipdb.set_trace()
        dns_records = self.cf.zones.dns_records.get(
            self.zone["id"], params={"name": self.subdomain}
        )
        self.assertTrue(dns_records)
        # cf.zones.dns_records.delete(subdomain_record.id)

        # Check that Sewer has requested and created a staging Let's Encrypt certificate
        # Use a time-out
        # Delete DNS records created for verification

        # Login is checked in test_oauth2.py
        # Only test that the OAuth2 application is correctly created

        # get domain list and expect created subdomain to be there
        # delete subdomain


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
            reverse("coordiantor-ping"), data=data, REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "This field is required", status_code=400)

        # Test passing invalid JSON
        data = "{hello there}"
        response = self.client.post(
            reverse("coordiantor-ping"),
            data=data,
            content_type="application/json",
            REMOTE_ADDR="1.1.1.1",
        )
        self.assertContains(response, "JSON parse error", status_code=400)

        # Test passing 127.0.0.1 as the remote IP address. Should fail as not routable
        data = {"local_ip_address": "192.168.0.2"}
        response = self.client.post(reverse("coordiantor-ping"), data=data)
        self.assertContains(response, "IP address is not routable", status_code=400)

        # Test a valid ping
        data = {"local_ip_address": "192.168.0.2"}
        response = self.client.post(
            reverse("coordiantor-ping"), data=data, REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "local_ip_address", status_code=201)
        self.assertContains(response, "external_ip_address", status_code=201)
        self.assertContains(response, "id", status_code=201)

        # Test another anonymous valid ping
        data = {"local_ip_address": "192.168.0.2"}
        response = self.client.post(
            reverse("coordiantor-ping"), data=data, REMOTE_ADDR="1.1.1.2"
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
            reverse("coordiantor-ping"), data=data, REMOTE_ADDR="1.1.1.2"
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
            reverse("coordiantor-ping"), data=data, REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "has been registered", status_code=403)
        self.assertContains(response, coordinator.id, status_code=403)
