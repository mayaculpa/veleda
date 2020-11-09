from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from farms.models import (
    ControllerComponent,
    ControllerComponentType,
    ControllerMessage,
    Site,
    SiteEntity,
)


class PermissionTests(TestCase):
    """Test the permission checking"""

    def setUp(self):
        self.user_a = get_user_model().objects.create_user(
            email="owner@a.com", password="foo"
        )
        self.user_b = get_user_model().objects.create_user(
            email="owner@b.com", password="foo"
        )
        self.controller_a = ControllerComponent.objects.create(
            component_type=ControllerComponentType.objects.create(name="TypeA"),
            site_entity=SiteEntity.objects.create(
                name="ControllerA",
                site=Site.objects.create(name="SiteA", owner=self.user_a),
            ),
            channel_name="some channel",
        )

    def test_controller_permission(self):
        """Check that the controller API checks permissions"""

        client = Client()
        client.force_login(self.user_a)
        controller_a_url = reverse(
            "controller-command", kwargs={"pk": str(self.controller_a.site_entity.id)}
        )
        response = client.post(
            controller_a_url,
            data={"type": ControllerMessage.COMMAND_TYPE},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        client.force_login(self.user_b)
        response = client.post(
            controller_a_url,
            data={"type": ControllerMessage.COMMAND_TYPE},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
