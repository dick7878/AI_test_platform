from django.contrib.auth.models import User
from django.test import TestCase

from .models import UserProfile


class UserProfileModelTests(TestCase):
    def test_create_user_profile(self) -> None:
        user = User.objects.create_user(username="u1", password="p@ssw0rd")
        profile = UserProfile.objects.create(user=user, dingtalk_id="dt_123")

        self.assertEqual(profile.user.username, "u1")
        self.assertEqual(profile.dingtalk_id, "dt_123")
