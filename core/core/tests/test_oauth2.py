from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from oauth2_provider.models import Application


class Oauth2Test(TestCase):
    def auth_redirect_test(self, view):
        """
        Tests that the selected oauth2 view redirects
        """
        response = self.http_client.get(reverse("oauth2_provider:" + view), follow=True)
        self.assertRedirects(
            response,
            "%s?next=%s" % (reverse("login"), reverse("oauth2_provider:" + view)),
        )

    def setUp(self):
        self.http_client = Client()
        self.api_client = APIClient()

        self.a_user = User.objects.create_user(
            username="a_user", email="a@example.com", password="12345"
        )
        self.super_user = User.objects.create_superuser(
            username="super_user", email="super@example.com", password="12345"
        )

        self.restricted_views = ["list", "register"]
        self.oauth2_client = Application.objects.create(
            client_id="1234",
            user=self.super_user,
            redirect_uris="localhost:8000",
            client_type="confidential",
            authorization_grant_type="hello",
            client_secret="abcd",
            name="test_client",
        )

    def tearDown(self):
        pass

    def test_application_with_anonymous_user(self):
        """
        Test anonymous user visiting the OAuth2 application pages
        """
        for view in self.restricted_views:
            self.auth_redirect_test(view)

    def test_application_with_normal_user(self):
        """
        Test a normal user visiting the OAuth2 application pages
        """
        self.http_client.login(username="a_user", password="12345")
        for view in self.restricted_views:
            self.auth_redirect_test(view)

    def test_application_with_super_user(self):
        """
        Test a super user visiting the OAuth2 application pages
        """
        self.http_client.login(username="super_user", password="12345")
        for view in self.restricted_views:
            response = self.http_client.get(reverse("oauth2_provider:" + view))
            self.assertEqual(response.status_code, 200)

        response = self.http_client.get(
            reverse("oauth2_provider:detail", kwargs={"pk": 1})
        )
        self.assertEqual(response.status_code, 200)
        response = self.http_client.get(
            reverse("oauth2_provider:detail", kwargs={"pk": 2})
        )
        self.assertEqual(response.status_code, 404)

