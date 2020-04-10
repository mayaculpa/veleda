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
from .forms import CoordinatorSetupRegistrationForm
from .models import Site, Coordinator, HydroponicSystem, Controller


class SiteTests(TestCase):
    def test_site_components(self):
        """Test creating a site and its components."""

        proto_site_owner = get_user_model().objects.create_user(
            email="owner@example.com", password="owners_passwd",
        )
        proto_site_owner.profile.short_name = "Dude"
        proto_site_owner.profile.full_name = "Dr. Owner C. Dude"
        proto_site_owner.save()

        proto_site_address = Address.objects.create(
            raw="Some Street 42, Any Town, Major City, New Country",
        )
        site = Site.objects.create(
            name="ProtoSite", owner=proto_site_owner, address=proto_site_address
        )
        self.assertEqual(
            site.owner.profile.short_name, proto_site_owner.profile.short_name
        )
        self.assertEqual(site.address.raw, proto_site_address.raw)

        coordinator = Coordinator.objects.create(
            site=site, local_ip_address="192.168.0.2", external_ip_address="1.1.1.1"
        )
        hydroponic_system_a = HydroponicSystem.objects.create(site=site,)
        hydroponic_system_b = HydroponicSystem.objects.create(site=site,)
        controller_a = Controller.objects.create(
            coordinator=coordinator,
            controller_type=Controller.SENSOR_TYPE,
            wifi_mac_address="00:11:22:33:44:55",
            external_ip_address="1.1.1.1",
        )
        controller_b = Controller.objects.create(
            coordinator=coordinator,
            controller_type=Controller.PUMP_TYPE,
            wifi_mac_address="00:11:22:33:44:56",
            external_ip_address="1.1.1.1",
        )
        self.assertEqual(Coordinator.objects.filter(site=site.id)[0].id, coordinator.id)
        self.assertEqual(controller_a.coordinator.id, coordinator.id)
        self.assertEqual(controller_b.coordinator.id, coordinator.id)
        self.assertEqual(hydroponic_system_a.site.id, site.id)
        self.assertEqual(hydroponic_system_b.site.id, site.id)

    def test_site_timestamps(self):
        """Test creating a site and check that the timestamps update correctly"""

        mocked_now = datetime.now(pytz.utc)
        with mock.patch("django.utils.timezone.now", return_value=mocked_now):
            site = Site.objects.create(name="ProtoSite")
            coordinator = Coordinator.objects.create(
                site=site, local_ip_address="192.168.0.2", external_ip_address="1.1.1.1"
            )
            hydroponic_system = HydroponicSystem.objects.create(
                site=site, system_type=HydroponicSystem.FLOOD_AND_DRAIN
            )
            controller = Controller.objects.create(
                coordinator=coordinator,
                controller_type=Controller.SENSOR_TYPE,
                wifi_mac_address="00:11:22:33:44:55",
                external_ip_address="1.1.1.1",
            )

        self.assertEqual(site.created_at, mocked_now)
        self.assertEqual(site.modified_at, mocked_now)
        self.assertEqual(coordinator.created_at, mocked_now)
        self.assertEqual(coordinator.modified_at, mocked_now)
        self.assertEqual(hydroponic_system.created_at, mocked_now)
        self.assertEqual(hydroponic_system.modified_at, mocked_now)
        self.assertEqual(controller.created_at, mocked_now)
        self.assertEqual(controller.modified_at, mocked_now)

        mocked_later = mocked_now + timedelta(hours=1)
        with mock.patch("django.utils.timezone.now", return_value=mocked_later):
            site.name = "New name"
            site.save()
            coordinator.local_ip_address = "192.168.0.2"
            coordinator.save()
            hydroponic_system.name = "A Flood and drain system"
            hydroponic_system.save()
            controller.wifi_mac_address = "11:22:33:44:55:66"
            controller.save()

        self.assertEqual(site.created_at, mocked_now)
        self.assertEqual(site.modified_at, mocked_later)
        self.assertEqual(coordinator.created_at, mocked_now)
        self.assertEqual(coordinator.modified_at, mocked_later)
        self.assertEqual(hydroponic_system.created_at, mocked_now)
        self.assertEqual(hydroponic_system.modified_at, mocked_later)
        self.assertEqual(controller.created_at, mocked_now)
        self.assertEqual(controller.modified_at, mocked_later)

    def test_controller_registration_flow(self):
        """Test a new controller automatically registering itself and being assigned to a site."""

        coordinator = Coordinator.objects.create(
            local_ip_address="192.168.0.2", external_ip_address="3.3.3.3"
        )
        controller_a = Controller.objects.create(
            wifi_mac_address="00:11:22:33:44:55", external_ip_address="3.3.3.3"
        )
        controller_b = Controller.objects.create(
            wifi_mac_address="00:11:22:33:44:56", external_ip_address="3.3.3.3"
        )
        controller_c = Controller.objects.create(
            wifi_mac_address="00:11:22:33:44:57", external_ip_address="4.4.4.4"
        )
        # Expect both to be unregistered
        unregistered_controllers = Controller.objects.get_local_unregistered(
            coordinator.external_ip_address
        )
        self.assertIn(controller_a, unregistered_controllers)
        self.assertIn(controller_b, unregistered_controllers)
        self.assertNotIn(controller_c, unregistered_controllers)

        controller_a.coordinator = coordinator
        controller_a.save()
        unregistered_controllers = Controller.objects.get_local_unregistered(
            coordinator.external_ip_address
        )
        self.assertNotIn(controller_a, unregistered_controllers)
        self.assertIn(controller_b, unregistered_controllers)
        self.assertNotIn(controller_c, unregistered_controllers)


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
            reverse("farms:coordinator-setup-select"), REMOTE_ADDR="127.0.0.1"
        )
        self.assertRedirects(
            response,
            reverse("login") + "?next=" + reverse("farms:coordinator-setup-select"),
        )

        # Test with authenticated user for remaining asserts
        self.client.login(username=self.user_a.email, password="user_a")

        # Test internal IP address
        response = self.client.get(
            reverse("farms:coordinator-setup-select"), REMOTE_ADDR="127.0.0.1"
        )
        self.assertContains(
            response, "external IP address can not be used for a lookup"
        )
        self.assertContains(response, "127.0.0.1")

        # Test empty setup page
        response = self.client.get(
            reverse("farms:coordinator-setup-select"), REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "no coordinators were found")

        # Test only registered coordinators
        site_a_1 = Site.objects.create(name="TestSite_A_1")
        site_a_2 = Site.objects.create(name="TestSite_A_2")
        coordinator_a_1 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1", site=site_a_1
        )
        coordinator_a_2 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1", site=site_a_2
        )
        response = self.client.get(
            reverse("farms:coordinator-setup-select"), REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, coordinator_a_1.site.name)
        self.assertContains(response, coordinator_a_2.site.name)
        self.assertContains(response, "None found")

        # Test listing unregistered coordinators
        coordinator_b_1 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        coordinator_b_2 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        response = self.client.get(
            reverse("farms:coordinator-setup-select"), REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, coordinator_b_1.id.hex[:7])
        self.assertContains(response, coordinator_b_2.id.hex[:7])

        # Test not showing coordinators for a user from a different subnet
        response = self.client.get(
            reverse("farms:coordinator-setup-select"), REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "no coordinators were found")

    def test_select_to_register(self):
        """Test that selecting a coordinator redirects to its registration"""

        # Test login required
        response = self.client.post(
            reverse("farms:coordinator-setup-select"), REMOTE_ADDR="127.0.0.1"
        )
        self.assertRedirects(
            response,
            reverse("login") + "?next=" + reverse("farms:coordinator-setup-select"),
        )

        # Test with a logged in user and valid coordinator for the remaining asserts
        self.client.login(username=self.user_a.email, password="user_a")
        coordinator_a_1 = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )

        # Test blank post request
        data = {}
        response = self.client.post(reverse("farms:coordinator-setup-select"), data)
        self.assertContains(response, "This field is required", status_code=400)

        # Test invalid UUID
        data = {"coordinator_id": coordinator_a_1.id.hex[:-1]}
        # import ipdb; ipdb.set_trace()
        response = self.client.post(reverse("farms:coordinator-setup-select"), data)
        self.assertContains(response, "Enter a valid UUID", status_code=400)

        # Test a valid request
        data = {"coordinator_id": coordinator_a_1.id}
        response = self.client.post(reverse("farms:coordinator-setup-select"), data)
        self.assertRedirects(
            response,
            reverse(
                "farms:coordinator-setup-register", kwargs={"pk": coordinator_a_1.id,}
            ),
        )

    def test_register_coordinator(self):
        """Test registering a coordinator"""

        # Test login required
        coordinator_a = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        response = self.client.get(
            reverse(
                "farms:coordinator-setup-register", kwargs={"pk": coordinator_a.id}
            ),
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertRedirects(
            response,
            reverse("login")
            + "?next="
            + reverse(
                "farms:coordinator-setup-register", kwargs={"pk": coordinator_a.id}
            ),
        )

        # Test if the form fields were loaded
        response = self.client.get(
            reverse(
                "farms:coordinator-setup-register", kwargs={"pk": coordinator_a.id}
            ),
            REMOTE_ADDR="127.0.0.1",
        )

    def test_coordinator_form(self):
        site = Site.objects.create(name="TestSite")
        sites = Site.objects.all()

        # Test a valid form
        data = {"subdomain_prefix": "valid-name", "site": site.id}
        form = CoordinatorSetupRegistrationForm(sites=sites, data=data)
        self.assertTrue(form.is_valid())

        # Test lowercasing
        data = {"subdomain_prefix": "Val1D-Name", "site": site.id}
        form = CoordinatorSetupRegistrationForm(sites=sites, data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["subdomain_prefix"], data["subdomain_prefix"].lower()
        )

        # Test underscores
        data = {"subdomain_prefix": "inVal1D_Name", "site": site.id}
        form = CoordinatorSetupRegistrationForm(sites=sites, data=data)
        self.assertFalse(form.is_valid())

        # Test dots
        data = {"subdomain_prefix": "inVal1D.Name", "site": site.id}
        form = CoordinatorSetupRegistrationForm(sites=sites, data=data)
        self.assertFalse(form.is_valid())

        # Test leading hyphen
        data = {"subdomain_prefix": "-inVal1DName", "site": site.id}
        form = CoordinatorSetupRegistrationForm(sites=sites, data=data)
        self.assertFalse(form.is_valid())

        # Test other characters
        data = {"subdomain_prefix": "a*ä", "site": site.id}
        form = CoordinatorSetupRegistrationForm(sites=sites, data=data)
        self.assertFalse(form.is_valid())


class SiteTemplateTests(TestCase):
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

    def test_create_site(self):
        """Test creating a site"""

        # Check required authentication
        response = self.client.get(reverse("farms:site-setup"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("farms:site-setup")
        )
        response = self.client.post(reverse("farms:site-setup"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("farms:site-setup")
        )

        with self.settings(
            STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
        ):
            self.client.login(username=self.user_a.email, password="user_a")
            response = self.client.get(reverse("farms:site-setup"))
            self.assertContains(response, "Name")
            self.assertContains(response, "Address")

            # Check poorly formatted requests
            data = {}
            response = self.client.post(reverse("farms:site-setup"), data)
            self.assertContains(response, "Site Setup", status_code=400)

            data = {"name": "test site"}
            response = self.client.post(reverse("farms:site-setup"), data)
            self.assertContains(response, "Site Setup", status_code=400)

            data = {"address": "some place"}
            response = self.client.post(reverse("farms:site-setup"), data)
            self.assertContains(response, "Site Setup", status_code=400)
            self.assertFalse(Site.objects.all())

            # Check valid requests
            data = {"name": "good site", "address": "some place"}
            response = self.client.post(reverse("farms:site-setup"), data)
            self.assertRedirects(response, reverse("farms:site-list"))
            self.assertTrue(Site.objects.all())

            site = Site.objects.get(name=data["name"])
            self.assertEqual(site.name, data["name"])
            self.assertEqual(site.owner, self.user_a)

    def test_site_list(self):
        """Test showing all sites registered to a user"""
        site_address_a = Address.objects.create(
            raw="Some Street 42, Any Town, Major City, New Country",
        )
        site_coordinator_a = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.1"
        )
        site_a = Site.objects.create(
            name="Site A", address=site_address_a, coordinator=site_coordinator_a
        )
        site_b = Site.objects.create(name="Site B")

        # Test required authentication
        response = self.client.get(reverse("farms:site-list"))
        self.assertRedirects(
            response, reverse("login") + "?next=" + reverse("farms:site-list")
        )

        # Test no owned sites
        self.client.login(username=self.user_a.email, password="user_a")
        response = self.client.get(reverse("farms:site-list"))
        self.assertContains(response, "Sites")
        self.assertContains(response, "No sites found")

        # Test one ownder site
        site_a.owner = self.user_a
        site_a.save()
        site_b.owner = self.user_b
        site_b.save()
        response = self.client.get(reverse("farms:site-list"))
        self.assertContains(response, site_a.name)
        self.assertNotContains(response, site_b.name)
        self.assertContains(response, site_address_a.raw)


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
        site = Site.objects.create(name="TestSite")
        coordinator = Coordinator.objects.create(
            site=site, local_ip_address="192.168.0.1", external_ip_address="1.1.1.3"
        )
        data = {"local_ip_address": "192.168.0.2", "id": coordinator.id}
        response = self.client.post(
            reverse("coordiantor-ping"), data=data, REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "Unauthenticated ping", status_code=403)
        self.assertContains(response, coordinator.id, status_code=403)


class ControllerAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        # Disable HTTP request warnings
        logging.disable()

    def tearDown(self):
        # Reenable HTTP request warnings
        logging.disable(logging.NOTSET)

    def test_controller_ping_post(self):
        """Test unregistered controllers pinging the server"""

        # Test passing an empty POST request
        data = {}
        response = self.client.post(
            reverse("controller-ping"), data=data, REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "This field is required", status_code=400)

        # Test passing 127.0.0.1 as the remote IP address. Should fail as not routable
        data = {"wifi_mac_address": "AA:BB:CC:DD:EE:FF"}
        ip_address = "127.0.0.1"
        response = self.client.post(
            reverse("controller-ping"), data=data, REMOTE_ADDR=ip_address
        )
        self.assertContains(response, "is not routable", status_code=400)
        self.assertContains(response, ip_address, status_code=400)

        # Test passing an IPv6 remote IP address. Should fail as not currently supported
        data = {"wifi_mac_address": "AA:BB:CC:DD:EE:FF"}
        ip_address = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        response = self.client.post(
            reverse("controller-ping"), data=data, REMOTE_ADDR=ip_address,
        )
        self.assertContains(response, "IPv6 address", status_code=400)
        self.assertContains(response, ip_address, status_code=400)

        # Test a valid ping
        data = {"wifi_mac_address": "AA:BB:CC:DD:EE:FF"}
        response = self.client.post(
            reverse("controller-ping"), data=data, REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "wifi_mac_address", status_code=201)
        self.assertContains(response, "external_ip_address", status_code=201)
        self.assertContains(response, "id", status_code=201)

        # Test another anonymous valid ping
        data = {"wifi_mac_address": "AA:BB:CC:DD:EE:FF"}
        response = self.client.post(
            reverse("controller-ping"), data=data, REMOTE_ADDR="1.1.1.1"
        )
        self.assertContains(response, "wifi_mac_address", status_code=201)
        self.assertContains(response, "external_ip_address", status_code=201)
        self.assertContains(response, "id", status_code=201)

        # Test a valid ping from a known coordinator
        data = {
            "wifi_mac_address": "AA:BB:CC:DD:EE:FF",
            id: json.loads(response.content)["id"],
        }
        response = self.client.post(
            reverse("controller-ping"), data=data, REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "wifi_mac_address", status_code=201)
        self.assertContains(response, "external_ip_address", status_code=201)
        self.assertContains(response, "id", status_code=201)

        # Register the coordinator and send an invalid ping. Expect the response to
        # contain the correct URL (consists of the coordinator-detail view + id)
        coordinator = Coordinator.objects.create(
            local_ip_address="127.0.0.1", external_ip_address="1.1.1.1"
        )
        controller = Controller.objects.create(
            coordinator=coordinator,
            wifi_mac_address="AA:BB:CC:DD:EE:FF",
            external_ip_address="1.1.1.1",
        )
        data = {"wifi_mac_address": "AA:BB:CC:DD:EE:FF", "id": controller.id}
        response = self.client.post(
            reverse("controller-ping"), data=data, REMOTE_ADDR="1.1.1.2"
        )
        self.assertContains(response, "Unauthenticated ping", status_code=403)
        self.assertContains(response, controller.id, status_code=403)

    def test_controller_ping_get(self):
        """Test unregistered controllers requesting local coordinators"""

        # Test passing 127.0.0.1 as the remote IP address. Should fail as not routable
        ip_address = "127.0.0.1"
        response = self.client.get(reverse("controller-ping"), REMOTE_ADDR=ip_address)
        self.assertContains(response, "is not routable", status_code=400)
        self.assertContains(response, ip_address, status_code=400)

        # Test passing an IPv6 remote IP address. Should fail as not currently supported
        ip_address = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        response = self.client.get(reverse("controller-ping"), REMOTE_ADDR=ip_address,)
        self.assertContains(response, "IPv6 address", status_code=400)
        self.assertContains(response, ip_address, status_code=400)

        # Test a valid ping. Result should be empty
        response = self.client.get(reverse("controller-ping"), REMOTE_ADDR="1.1.1.1")
        self.assertFalse(json.loads(response.content)["coordinator_local_ip_address"])
        self.assertEqual(response.status_code, 200)

        # Test a valid ping. Should not return coordinator from different subnet
        coordinator = Coordinator.objects.create(
            local_ip_address="192.168.0.1", external_ip_address="1.1.1.2"
        )
        ip_address = "1.1.1.1"
        self.assertNotEqual(coordinator.external_ip_address, ip_address)
        response = self.client.get(reverse("controller-ping"), REMOTE_ADDR=ip_address)
        self.assertFalse(json.loads(response.content)["coordinator_local_ip_address"])
        self.assertEqual(response.status_code, 200)

        # Test a valid ping. Should return coordinator from the same subnet
        ip_address = coordinator.external_ip_address
        response = self.client.get(reverse("controller-ping"), REMOTE_ADDR=ip_address)
        self.assertEqual(
            json.loads(response.content)["coordinator_local_ip_address"],
            coordinator.local_ip_address,
        )
        self.assertEqual(response.status_code, 200)
