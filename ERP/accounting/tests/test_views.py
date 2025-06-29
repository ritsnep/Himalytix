"""
View tests for accounting views and HTMX endpoints.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class FiscalYearViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='test')
        self.client.force_login(self.user)

    def test_fiscal_year_list_view(self):
        response = self.client.get(reverse('accounting:fiscal_year_list'))
        self.assertEqual(response.status_code, 200)


class VoucherEntryViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        from usermanagement.models import Organization, UserOrganization
        from accounting.models import FiscalYear, AccountingPeriod, JournalType, VoucherModeConfig, Currency

        self.org = Organization.objects.create(name="Org", code="ORG", type="company")
        self.user = User.objects.create_user(username="user1", password="pass", role="superadmin")
        UserOrganization.objects.create(user=self.user, organization=self.org, is_active=True)

        self.fy = FiscalYear.objects.create(
            organization=self.org,
            code="FY1",
            name="2024",
            start_date="2024-01-01",
            end_date="2024-12-31",
            is_current=True,
        )
        self.period = AccountingPeriod.objects.create(
            fiscal_year=self.fy,
            period_number=1,
            name="P1",
            start_date="2024-01-01",
            end_date="2024-01-31",
            is_current=True,
        )
        self.journal_type = JournalType.objects.create(
            organization=self.org,
            code="GEN",
            name="General",
        )
        Currency.objects.create(currency_code="USD", currency_name="US Dollar", symbol="$")
        VoucherModeConfig.objects.create(
            organization=self.org,
            code="VC1",
            name="Default",
            journal_type=self.journal_type,
            is_default=True,
            default_currency="USD",
        )

        self.client.force_login(self.user)

    def test_voucher_entry_hides_right_sidebar(self):
        response = self.client.get(reverse('accounting:voucher_entry'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Theme Customizer')