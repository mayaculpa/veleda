from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase, TransactionTestCase
from django.urls.base import reverse
from rest_framework.authtoken.models import Token
from iot.models import ControllerComponent, ControllerComponentType, Site, SiteEntity


class SiteTests(TestCase):
    """Test views connected to sites."""

    def setUp(self):
        self.client = Client()
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self.owner_z = get_user_model().objects.create_user(
            email="ownerZ@bar.com", password="foo"
        )
        self.empty_owner = get_user_model().objects.create_user(
            email="emtpy@bar.com", password="foo"
        )
        self.site_a = Site.objects.create(name="Site A", owner=self.owner_a)
        self.site_b = Site.objects.create(name="Site B", owner=self.owner_a)
        self.site_z = Site.objects.create(name="Site C", owner=self.owner_z)

    def test_list(self):
        """Check the listing of sites."""

        # Check login required
        url = reverse("iot:site-list")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Check that all sites and their info are listed
        self.client.force_login(self.owner_a)
        response = self.client.get(url)
        self.assertContains(response, self.site_a.name)
        self.assertContains(response, self.site_b.name)
        self.assertNotContains(response, self.site_z.name)

        # Test the view for a new user
        self.client.force_login(self.empty_owner)
        response = self.client.get(url)
        self.assertContains(response, "No sites found")
        self.assertContains(response, reverse("iot:create-site"))

    def test_create(self):
        """Check the creation of sites."""

        # Check login required
        url = reverse("iot:create-site")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Check the form to create a site
        self.client.force_login(self.owner_a)
        response = self.client.get(url)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, "name")
        self.assertContains(response, "address")

        # Check request to create a site
        data = {"name": "NewSite", "address": "hi there"}
        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse("iot:site-list"))
        self.assertEqual(Site.objects.filter(name=data["name"]).count(), 1)

        # Check a bad request to create a site
        data = {"name": "NewSite"}
        response = self.client.post(url, data=data)
        self.assertTrue(response.status_code >= 400 and response.status_code < 500)

    def test_delete(self):
        """Check the deletion of sites."""

        # Check login required
        url = reverse("iot:delete-site", kwargs={"pk": self.site_a.pk})
        response = self.client.post(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Test deleting a site
        self.client.force_login(self.owner_a)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("iot:site-list"))
        self.assertEqual(Site.objects.filter(owner=self.owner_a).count(), 1)


class ControllerTests(TestCase):
    """Test views connected to controllers"""

    def setUp(self):
        self.client = Client()
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self.owner_z = get_user_model().objects.create_user(
            email="ownerZ@bar.com", password="foo"
        )
        self.site_a = Site.objects.create(name="Site A", owner=self.owner_a)
        self.site_b = Site.objects.create(name="Site B", owner=self.owner_a)
        self.site_z = Site.objects.create(name="Site C", owner=self.owner_z)

        self.esp32 = ControllerComponentType.objects.create(name="ESP32")
        self.esp_a = ControllerComponentType.objects.create(
            name="ESP_A", created_by=self.owner_a
        )
        self.esp_z = ControllerComponentType.objects.create(
            name="ESP_Z", created_by=self.owner_z
        )
        self.controller_a_1 = ControllerComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="CtrlA1", site=self.site_a),
            component_type=self.esp32,
        )
        self.controller_a_2 = ControllerComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="CtrlA2", site=self.site_a),
            component_type=self.esp32,
        )
        self.controller_b_1 = ControllerComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="CtrlB1", site=self.site_b),
            component_type=self.esp_a,
        )
        self.controller_z_1 = ControllerComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="CtrlZ1", site=self.site_z),
            component_type=self.esp32,
        )

    def test_list(self):
        """Check the listing of controllers."""

        # Check login required
        url = reverse("iot:controller-list")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Test listing the owner's controllers
        self.client.force_login(self.owner_a)
        response = self.client.get(url)
        self.assertContains(response, self.controller_a_1.site_entity.name)
        self.assertContains(response, self.controller_a_2.site_entity.name)
        self.assertContains(response, self.controller_b_1.site_entity.name)
        self.assertNotContains(response, self.controller_z_1.site_entity.name)

    def test_create(self):
        """Check the creation of controllers."""

        # Check login required
        url = reverse("iot:create-controller")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Check create form
        self.client.force_login(self.owner_a)
        response = self.client.get(url)
        self.assertContains(response, self.site_a.name)
        self.assertNotContains(response, self.site_z.name)
        self.assertContains(response, self.esp32.name)
        self.assertContains(response, self.esp_a.name)
        self.assertNotContains(response, self.esp_z.name)

        # Test creating with invalid site
        data = {
            "name": "NewCtrl1",
            "site": str(self.site_z.pk),
            "controller_component_type": str(self.esp32.pk),
        }
        response = self.client.post(url, data=data)
        self.assertTrue(response.status_code >= 400 and response.status_code < 500)

        # Test creating with invalid type
        data = {
            "name": "NewCtrl2",
            "site": str(self.site_a.pk),
            "controller_component_type": str(self.esp_z.pk),
        }
        response = self.client.post(url, data=data)
        self.assertTrue(response.status_code >= 400 and response.status_code < 500)

        # Test that a new type is created
        data = {
            "name": "NewCtrl3",
            "site": str(self.site_a.pk),
            "controller_component_type": str(self.esp_a.pk),
            "new_type_name": "SomeNewType",
        }
        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse("iot:controller-list"))
        self.assertTrue(
            ControllerComponentType.objects.filter(name=data["new_type_name"]).count()
        )
        self.assertTrue(
            ControllerComponent.objects.filter(site_entity__name=data["name"]).count()
        )

        # Test that an existing type is used
        data = {
            "name": "NewCtrl4",
            "site": str(self.site_a.pk),
            "controller_component_type": str(self.esp_a.pk),
        }
        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse("iot:controller-list"))
        controller = ControllerComponent.objects.get(site_entity__name=data["name"])
        self.assertTrue(controller)
        self.assertEqual(
            str(controller.component_type_id), data["controller_component_type"]
        )

    def test_delete(self):
        """Test deletion of controllers."""

        # Check login required
        url = reverse("iot:delete-controller", kwargs={"pk": self.controller_a_1.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Test deleting another user's controller
        self.client.force_login(self.owner_z)
        response = self.client.post(url)
        self.assertTrue(
            ControllerComponent.objects.filter(pk=self.controller_a_1).count()
        )
        self.assertRedirects(response, reverse("iot:controller-list"))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")

        # Test deleting a controller
        self.client.force_login(self.owner_a)
        response = self.client.post(url)
        self.assertFalse(
            ControllerComponent.objects.filter(pk=self.controller_a_1).count()
        )
        self.assertRedirects(response, reverse("iot:controller-list"))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")


class UserTokenTests(TestCase):
    """Test creating and deleting user tokens."""

    def setUp(self):
        self.client = Client()
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self.owner_z = get_user_model().objects.create_user(
            email="ownerZ@bar.com", password="foo"
        )
    
    def test_create(self):
        """Test creating a user auth token."""

        # Check login required
        url = reverse("iot:create-user-token")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Check that a token has been created
        self.client.force_login(self.owner_a)
        with self.assertRaises(Token.DoesNotExist):
            _ = self.owner_a.auth_token
        response = self.client.post(url)
        self.owner_a.refresh_from_db()
        self.assertTrue(self.owner_a.auth_token)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")

        # Check creating a token again
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].tags, "success")


    def test_delete(self):
        """Test creating a user auth token."""

        # Check login required
        url = reverse("iot:delete-user-token")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

        # Check that a token has been deleted
        Token.objects.create(user=self.owner_a, key=Token.generate_key())
        self.client.force_login(self.owner_a)
        response = self.client.post(url)
        self.owner_a.refresh_from_db()
        with self.assertRaises(Token.DoesNotExist):
            _ = self.owner_a.auth_token
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")

        # Check error handling for no tokens found
        response = self.client.post(url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].tags, "error")

