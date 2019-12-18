import base64
import urllib
import json
import logging
from uuid import uuid4

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from oauth2_provider.models import Application


class Oauth2ApplicationTests(TestCase):
    """
    Tests the OAuth2 functionality
    """

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

        User = get_user_model()
        self.a_user = User.objects.create_user(
            email="user@example.com", password="12345"
        )
        self.super_user = User.objects.create_superuser(
            email="super@example.com", password="12345"
        )

        self.restricted_views = ["list", "register"]
        self.oauth2_client = Application.objects.create(
            client_id="1234",
            client_secret="abcd",
            user=self.super_user,
            redirect_uris="localhost:8000",
            client_type="confidential",
            authorization_grant_type="authorization-code",
            name="test_client",
        )
        # Disable HTTP request warnings
        logging.disable()

    def tearDown(self):
        # Reenable HTTP request warnings
        logging.disable(logging.NOTSET)

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
        self.http_client.login(email="user@example.com", password="12345")
        for view in self.restricted_views:
            self.auth_redirect_test(view)

    def test_application_with_super_user(self):
        """
        Test a super user visiting the OAuth2 application pages
        """
        self.http_client.login(email="super@example.com", password="12345")
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


class Oauth2AuthenticationTests(TestCase):
    """
    Tests the OAuth2 authentication
    """

    def setUp(self):
        User = get_user_model()
        self.a_user = User.objects.create_user(
            email="user@example.com", password="12345"
        )
        self.super_user = User.objects.create_superuser(
            email="super@example.com", password="12345"
        )

        self.oauth2_client = Application.objects.create(
            client_id="1234",
            client_secret="abcd",
            user=self.super_user,
            redirect_uris="http://oauth2_client_ip/callback",
            client_type="confidential",
            authorization_grant_type="authorization-code",
            name="test_client",
        )
        self.oauth2_client.save()

    def tearDown(self):
        pass

    def test_authorization_flow(self):
        state = str(uuid4())
        params = {
            "client_id": self.oauth2_client.client_id,
            "response_type": "code",
            "state": state,
            "redirect_uri": self.oauth2_client.redirect_uris,
            "duration": 3600,
            "scope": "userinfo-v1",
        }
        authorize_url = (
            reverse("oauth2_provider:authorize") + "?" + urllib.parse.urlencode(params)
        )

        # Request the authorization form
        authorization_client = Client()
        self.assertTrue(
            authorization_client.login(email="user@example.com", password="12345")
        )
        response = authorization_client.get(authorize_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Submit the authorization form
        authorization_data = {
            "csrfmiddlewaretoken": response.context["csrf_token"].__str__(),
            "allow": "Authorize",
            "redirect_uri": response.context_data["redirect_uri"],
            "scope": response.context_data["scopes"][0],
            "client_id": response.context_data["client_id"],
            "state": response.context_data["state"],
            "response_type": response.context_data["response_type"],
        }
        response = authorization_client.post(authorize_url, authorization_data)
        self.assertEqual(response.status_code, 302)

        # Parse the redirect and request an access token
        token_client = Client()

        auth_string = (
            self.oauth2_client.client_id + ":" + self.oauth2_client.client_secret
        )
        credentials = base64.b64encode(auth_string.encode())
        token_client.defaults["HTTP_AUTHORIZATION"] = "Basic " + credentials.decode(
            "ascii"
        )

        response_data = urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)
        token_data = {
            "grant_type": "authorization_code",
            "code": response_data["code"][0],
            "redirect_uri": self.oauth2_client.redirect_uris,
        }

        response = token_client.post(reverse("oauth2_provider:token"), data=token_data)
        token_json = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", token_json)

        # Request user data with obtained token and verify identity
        userinfo_client = Client()
        userinfo_client.defaults["HTTP_AUTHORIZATION"] = (
            "Bearer " + token_json["access_token"]
        )

        response = userinfo_client.get(reverse("api-v1-userinfo"))
        self.assertEqual(response.status_code, 200)
        userinfo_json = json.loads(response.content)
        self.assertEqual(userinfo_json["email"], self.a_user.email)
        self.assertNotEqual(userinfo_json["email"], self.super_user.email)

