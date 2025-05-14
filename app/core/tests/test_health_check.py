"""
Test the health check endpoint
"""

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


class TestHealthCheck(TestCase):
    """
    Test the health check endpoint
    """

    def test_health_check(self):
        client = APIClient()
        response = client.get(reverse("health-check"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})
