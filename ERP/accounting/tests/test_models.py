"""
Unit tests for accounting models.
"""
from django.test import TestCase
from accounting.models import FiscalYear

class FiscalYearModelTest(TestCase):
    def test_str(self):
        fy = FiscalYear(code='FY24', name='2024', start_date='2024-01-01', end_date='2024-12-31')
        self.assertEqual(str(fy), 'FY24 - 2024')
