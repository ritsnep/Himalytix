from django.test import TestCase
from .models import CustomUser, Organization

class CustomUserTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org", code="TST", type="company")
    def test_create_user(self):
        user = CustomUser.objects.create_user(username="testuser", password="pass", organization=self.org)
        self.assertEqual(user.username, "testuser")