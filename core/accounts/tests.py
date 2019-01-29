from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model


class LoginTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        User = get_user_model()
        self.a_user = User.objects.create_user(
            email="jake.john@example.com", password="jakes_passwd"
        )
        self.staff_user = User.objects.create_user(
            email="staffy@example.com", password="staffys_passwd", is_staff=True
        )
        self.super_user = User.objects.create_superuser(
            email="super@example.com", password="super_passwd"
        )

    def test_fail_login_only_email(self):
        pass
