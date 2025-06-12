import pytest
from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
def test_htmx_sidebar_partial_returns_fragment():
    client = Client()
    url = reverse('accounting:chart_of_accounts_list_hx')
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert b'<html' not in response.content.lower()