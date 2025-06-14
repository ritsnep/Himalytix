"""
View tests for accounting views and HTMX endpoints.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class FiscalYearViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')

    def test_fiscal_year_list_view(self):
        response = self.client.get(reverse('accounting:fiscal_year_list'))
        self.assertEqual(response.status_code, 200)
