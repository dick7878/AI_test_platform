from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import UserProfile


class UserProfileModelTests(TestCase):
    def test_create_user_profile(self) -> None:
        user = User.objects.create_user(username="u1", password="p@ssw0rd")
        profile = UserProfile.objects.create(user=user, dingtalk_id="dt_123")

        self.assertEqual(profile.user.username, "u1")
        self.assertEqual(profile.dingtalk_id, "dt_123")


class DevLoginApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username="dev_user", password="p@ssw0rd")

    def test_dev_login_success(self) -> None:
        response = self.client.post(
            "/api/dev/login/",
            {"username": "dev_user", "password": "p@ssw0rd"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "dev_user")

    def test_dev_login_invalid_password(self) -> None:
        response = self.client.post(
            "/api/dev/login/",
            {"username": "dev_user", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_dev_logout_success(self) -> None:
        login_response = self.client.post(
            "/api/dev/login/",
            {"username": "dev_user", "password": "p@ssw0rd"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)

        logout_response = self.client.post("/api/dev/logout/", {}, format="json")
        self.assertEqual(logout_response.status_code, 200)
