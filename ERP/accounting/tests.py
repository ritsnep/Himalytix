from django.test import TestCase
from .models import FiscalYear, Organization
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class FiscalYearModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org", code="TST", type="company")
    def test_create_fiscal_year(self):
        fy = FiscalYear.objects.create(
            organization=self.org,
            code="FY01",
            name="2024",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        self.assertEqual(str(fy), "FY01 - 2024")


class PermissionRedirectTests(TestCase):
    databases = {'default'}

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="user", password="pass", role="user")

    def test_fiscal_year_list_redirects_without_org(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('accounting:fiscal_year_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('select-organization', resp.url)