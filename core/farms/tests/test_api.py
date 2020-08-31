import json
import logging

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from ..models import Site, Coordinator, Controller


class SiteAPITests(TestCase):
    """Test the site REST API endpoints"""

    def setUp(self):
        self.client = Client()
        # Disable HTTP request warnings
        logging.disable()

        # Create 3 users, with total 2, 1, and 0 sites respectively
        self.user_a = get_user_model().objects.create_user(
            email="user_a@example.com", password="passwd_a",
        )
        self.user_b = get_user_model().objects.create_user(
            email="user_b@example.com", password="passwd_b",
        )
        self.user_c = get_user_model().objects.create_user(
            email="user_c@example.com", password="passwd_c",
        )
        self.site_a1 = Site.objects.create(name="Site A1", owner=self.user_a)
        self.site_a2 = Site.objects.create(name="Site A2", owner=self.user_a)
        self.site_b1 = Site.objects.create(name="Site B1", owner=self.user_b)

    def tearDown(self):
        # Reenable HTP request warnings
        logging.disable(logging.NOTSET)

    def test_site_list(self):
        """Test that the list of owned sites are shown"""

        # Check that authentication is required
        response = self.client.get(reverse("site-list"))
        self.assertContains(response, "Authentication credentials", status_code=401)

        # Check that the sites of the first user are listed
        self.assertTrue(
            self.client.login(username=self.user_a.email, password="passwd_a")
        )
        response = self.client.get(reverse("site-list"))
        self.assertContains(response, self.site_a1.name)
        self.assertContains(response, self.site_a2.name)
        self.assertNotContains(response, self.site_b1.name)

        # Check the sites of the second user
        self.assertTrue(
            self.client.login(username=self.user_b.email, password="passwd_b")
        )
        response = self.client.get(reverse("site-list"))
        self.assertNotContains(response, self.site_a1.name)
        self.assertNotContains(response, self.site_a2.name)
        self.assertContains(response, self.site_b1.name)

        # Check that the last user not shown any sites
        self.assertTrue(
            self.client.login(username=self.user_c.email, password="passwd_c")
        )
        response = self.client.get(reverse("site-list"))
        self.assertEqual(response.content, b"[]")

    def test_site_details(self):
        """Test that the details of a site are shown"""

        # Check that authentication is required
        response = self.client.get(
            reverse("site-detail", kwargs={"pk": self.site_a1.id})
        )
        self.assertContains(response, "Authentication credentials", status_code=401)

        # Check that a user can only see their own sites
        self.assertTrue(
            self.client.login(username=self.user_a.email, password="passwd_a")
        )
        response = self.client.get(
            reverse("site-detail", kwargs={"pk": self.site_b1.id})
        )
        self.assertContains(response, "Not found", status_code=404)
        response = self.client.get(
            reverse("site-detail", kwargs={"pk": self.site_a2.id})
        )
        self.assertContains(response, self.site_a2.name)

        # Check that a link from the list view to the detail site works
        response = self.client.get(reverse("site-list"))
        self.assertContains(
            response, reverse("site-detail", kwargs={"pk": self.site_a1.id})
        )
        self.assertNotContains(
            response, reverse("site-detail", kwargs={"pk": self.site_b1.id})
        )

    def test_create_update_delete_site(self):
        """Test the creation of sites via the API"""

        # Create a site from list view
        logged_in = self.client.login(username=self.user_a.email, password="passwd_a")
        self.assertTrue(logged_in)
        data = {
            "name": "Site A3",
            "address": {"raw": "Some street 22, Some City, Some Country",},
        }
        response = self.client.post(
            reverse("site-list"), data=data, content_type="application/json"
        )

        self.assertContains(response, data["name"], status_code=201)
        self.assertContains(response, data["address"]["raw"], status_code=201)

        # Put a site
        put_data = json.loads(response.content)
        put_data["name"] = "Void Site A3 Void"
        response = self.client.put(
            put_data["url"], data=put_data, content_type="application/json"
        )

        self.assertContains(response, put_data["name"])
        self.assertContains(response, put_data["address"]["raw"])

        # Patch a site
        patch_data = {"name": "New Site A3 New"}
        response = self.client.patch(
            put_data["url"], data=patch_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 405)

        # Delete a site
        response = self.client.delete(put_data["url"])
        self.assertEqual(response.status_code, 204)


class CoordinatorAPITests(TransactionTestCase):
    """Test the coordinator REST API endpoints"""

    def setUp(self):
        self.client = Client()
        # Disable HTTP request warnings
        logging.disable()

        # Create coordinators and some sites
        self.user_a = get_user_model().objects.create_user(
            email="user_a@example.com", password="passwd_a"
        )
        self.user_b = get_user_model().objects.create_user(
            email="user_b@example.com", password="passwd_b"
        )
        self.site_a1 = Site.objects.create(name="Site A", owner=self.user_a)
        self.coordinator_a1 = Coordinator.objects.create(
            site=self.site_a1,
            local_ip_address="10.0.0.2",
            external_ip_address="1.1.1.1",
        )
        self.site_a2 = Site.objects.create(name="Site A2", owner=self.user_a)
        self.coordinator_a2 = Coordinator.objects.create(
            site=self.site_a2,
            local_ip_address="10.0.0.2",
            external_ip_address="1.1.1.2",
        )

    def tearDown(self):
        # Reenable HTTP request warnings
        logging.disable(logging.NOTSET)

    def test_coordinator_list(self):
        """Test listing coordinators with the REST API"""

        # Check that authentication is required
        response = self.client.get(reverse("coordinator-list"))
        self.assertContains(response, "Authentication credentials", status_code=401)

        # Check that users find their own coordinators
        logged_in = self.client.login(username=self.user_a.email, password="passwd_a")
        self.assertTrue(logged_in)
        response = self.client.get(reverse("coordinator-list"))
        self.assertContains(response, self.coordinator_a1.external_ip_address)
        self.assertContains(response, self.site_a2.id)

        # Check that users can only see their own coordinators
        logged_in = self.client.login(username=self.user_b.email, password="passwd_b")
        self.assertTrue(logged_in)
        response = self.client.get(reverse("coordinator-list"))
        self.assertNotContains(response, self.coordinator_a1.external_ip_address)
        self.assertNotContains(response, self.site_a2.id)

    def test_coordinator_details(self):
        """Test that the details of a coordinator are shown"""

        # Check that authentication is required
        response = self.client.get(
            reverse("coordinator-detail", kwargs={"pk": self.coordinator_a1.id})
        )
        self.assertContains(response, "Authentication credentials", status_code=401)

        # Check that a user can see the details of their coordinator
        logged_in = self.client.login(username=self.user_a.email, password="passwd_a")
        self.assertTrue(logged_in)
        response = self.client.get(
            reverse("coordinator-detail", kwargs={"pk": self.coordinator_a1.id})
        )
        self.assertContains(response, self.coordinator_a1.external_ip_address)
        self.assertContains(response, self.coordinator_a1.id)

        # Check that users cannot see details of other's coordinators
        logged_in = self.client.login(username=self.user_b.email, password="passwd_b")
        self.assertTrue(logged_in)
        response = self.client.get(
            reverse("coordinator-detail", kwargs={"pk": self.coordinator_a1.id})
        )
        self.assertEqual(response.status_code, 404)

    def test_limit_site_listing(self):
        """Check that a user can not set the sites of other users. This prevents data
           leaks in browsable API"""

        # First test a valid case
        logged_in = self.client.login(username=self.user_a.email, password="passwd_a")
        self.assertTrue(logged_in)
        data = {
            "site": reverse("site-detail", kwargs={"pk": self.site_a1.id}),
            "local_ip_address": "10.0.0.2",
            "external_ip_address": "1.1.2.1",
        }
        response = self.client.post(
            reverse("coordinator-list"), data=data, content_type="application/json"
        )
        self.assertContains(response, self.site_a1.id, status_code=201)
        self.assertContains(response, data["local_ip_address"], status_code=201)

        # Then a request that should be blocked
        logged_in = self.client.login(username=self.user_b.email, password="passwd_b")
        self.assertTrue(logged_in)
        data = {
            "site": reverse("site-detail", kwargs={"pk": self.site_a1.id}),
            "local_ip_address": "10.0.0.2",
            "external_ip_address": "1.1.2.2",
        }
        response = self.client.post(
            reverse("coordinator-list"), data=data, content_type="application/json"
        )
        self.assertNotContains(response, self.site_a1.id, status_code=400)
        self.assertContains(response, "Invalid hyperlink", status_code=400)

    def test_create_update_delete_flow(self):
        """Test the creating, updating and deleting coordinators"""

        # Create a coordinator from list view
        logged_in = self.client.login(username=self.user_a.email, password="passwd_a")
        self.assertTrue(logged_in)
        site_a3 = Site.objects.create(name="Site A3", owner=self.user_a)
        data = {
            "site": reverse("site-detail", kwargs={"pk": site_a3.id}),
            "local_ip_address": "10.0.0.2",
            "external_ip_address": "1.1.2.1",
            "password": "coord_a3_passwd",
        }
        response = self.client.post(
            reverse("coordinator-list"), data=data, content_type="application/json"
        )
        self.assertContains(response, site_a3.id, status_code=201)
        self.assertContains(response, data["local_ip_address"], status_code=201)

        # Put a coordinator
        put_data = json.loads(response.content)
        put_data["local_ip_address"] = "10.0.0.5"
        response = self.client.put(
            put_data["url"], data=put_data, content_type="application/json"
        )

        self.assertContains(response, put_data["local_ip_address"])
        self.assertContains(response, put_data["external_ip_address"])

        # Patch a coordinator
        patch_data = {"local_ip_address": "10.0.0.6"}
        response = self.client.patch(
            put_data["url"], data=patch_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 405)

        # Delete a coordinator
        response = self.client.delete(put_data["url"])
        self.assertEqual(response.status_code, 204)

    def test_update_password(self):
        """Test a coordinator's login functionality"""

        # Creating a coordiantor without password should not create a user
        self.assertFalse(self.coordinator_a1.user)

        # Create a coordinator with a user account check that a user was created
        logged_in = self.client.login(username=self.user_a.email, password="passwd_a")
        self.assertTrue(logged_in)
        data = {
            "site": reverse("site-detail", kwargs={"pk": self.site_a1.id}),
            "local_ip_address": "10.0.0.2",
            "external_ip_address": "1.1.2.1",
            "password": "pass123",
        }
        response = self.client.post(
            reverse("coordinator-list"), data=data, content_type="application/json"
        )
        # Check that a user instance was created
        json_response = json.loads(response.content)
        self.assertTrue(get_user_model().objects.get(email=json_response["email"]))
        # Check that it is possible to login with those credentials
        logged_in = Client().login(
            username=json_response["email"], password=data["password"]
        )
        self.assertTrue(logged_in)

        # Add a user account to an existing coordinator, then update the password
        for i in range(2):
            response = self.client.get(
                reverse("coordinator-detail", kwargs={"pk": self.coordinator_a1.id})
            )
            put_data = json.loads(response.content)
            put_data["password"] = f"passwd{i}"
            response = self.client.put(
                put_data["url"], data=put_data, content_type="application/json"
            )
            # Check that a user instance was created
            self.assertTrue(
                get_user_model().objects.get(email=self.coordinator_a1.get_email_address())
            )
            # Check that it is possible to login with those credentials
            logged_in = Client().login(
                username=json.loads(response.content)["email"], password=put_data["password"]
            )
            self.assertTrue(logged_in)


class CoordinatorPingAPITests(TestCase):
    """Test the coordinator ping API endpoints"""

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
    """Test the controller REST API endpoints"""

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
