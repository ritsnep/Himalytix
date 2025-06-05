from django.test import TestCase
from .models import FiscalYear, Organization

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