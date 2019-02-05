from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_integration_create_user(self):
        """Test successfully creating a new user"""

        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 200)
        fields = response.context_data["form"].fields
        self.assertIn("email", fields)
        self.assertIn("password1", fields)
        self.assertIn("password2", fields)

        user_data = {
            "email": "jake@example.com",
            "password1": "jakes_passwd",
            "password2": "jakes_passwd",
        }
        reponse = self.client.post(reverse("accounts:signup"), data=user_data)
        self.assertRedirects(reponse, reverse("django_registration_complete"))

        jake = get_user_model().objects.get(email=user_data["email"])
        self.assertEqual(jake.email, user_data["email"])

    def test_integration_create_user_errors(self):
        """Test data verification when creating a new user"""

        a_user = get_user_model().objects.create_user(
            email="jake.john@example.com", password="jakes_passwd"
        )

        user_data = {
            "email": a_user.email,
            "password1": "jakes_passwd",
            "password2": "jakes_passwd",
        }
        reponse = self.client.post(reverse("accounts:signup"), data=user_data)
        self.assertIn("email", reponse.context_data["form"].errors)

        user_data = {
            "email": "not_jake@example.com",
            "password1": "jakes_passwd",
            "password2": "not_jakes_passwd",
        }
        reponse = self.client.post(reverse("accounts:signup"), data=user_data)
        self.assertIn("password2", reponse.context_data["form"].errors)

        user_data["password2"] = ""
        reponse = self.client.post(reverse("accounts:signup"), data=user_data)
        self.assertIn("password2", reponse.context_data["form"].errors)

    def test_create_users(self):
        """Test creating different types of users"""

        user_manager = get_user_model().objects
        jake = user_manager.create_user(
            email="jake@example.com", password="jakes_passwd"
        )
        self.assertEqual(jake, user_manager.get(email=jake.email))
        self.assertTrue(jake.is_active)
        self.assertFalse(jake.is_staff)
        self.assertFalse(jake.is_superuser)
        self.assertEqual(str(jake), jake.email)
        self.assertEqual(jake.get_full_name(), jake.email)
        self.assertEqual(jake.get_short_name(), jake.email)

        staff = user_manager.create_user(
            email="staff@example.com", is_staff=True, password="staffs_passwd"
        )
        self.assertEqual(staff, user_manager.get(email=staff.email))
        self.assertTrue(staff.is_active)
        self.assertTrue(staff.is_staff)
        self.assertFalse(staff.is_superuser)

        superuser = user_manager.create_superuser(
            email="super@example.com", password="supers_passwd"
        )
        self.assertEqual(superuser, user_manager.get(email=superuser.email))
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

        with self.assertRaises(ValueError):
            user_manager.create_user(email=None)

        with self.assertRaises(ValueError):
            user_manager.create_superuser(
                email="super1@example.com", is_staff=False, password="supers_passwd"
            )

        with self.assertRaises(ValueError):
            user_manager.create_superuser(
                email="super2@example.com", is_superuser=False, password="supers_passwd"
            )

    def test_modify_profile(self):
        user_manager = get_user_model().objects
        jake = user_manager.create_user(
            email="jake@example.com", password="jakes_passwd"
        )
        self.assertEqual(jake.get_short_name(), jake.email)
        jake.profile.short_name = "Jake"
        jake.profile.full_name = "Sir Jake Richard III"
        jake.save()

        new_jake = user_manager.get(id=jake.id)
        self.assertEqual(new_jake.profile.full_name, jake.profile.full_name)
        self.assertEqual(new_jake.get_short_name(), jake.profile.short_name)
        self.assertEqual(str(new_jake), jake.profile.full_name)
        self.assertEqual(str(new_jake.profile), jake.profile.full_name)

        kate = get_user_model()(email="kate@katey.com")
        self.assertEqual(kate.get_short_name(), kate.email)
        self.assertEqual(kate.get_full_name(), kate.email)

