from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from tax.models import Client, TaxCase


class TaxCaseListAPITests(TestCase):

    def setUp(self):
        self.api_client = APIClient()

        self.client_obj = Client.objects.create(
            name="Rahul Kumar",
        )

        self.tax_case = TaxCase.objects.create(
            client=self.client_obj,
            tax_year=2025,
            filing_status=TaxCase.FilingStatus.MARRIED_JOINTLY,
        )

        self.url = reverse("tax-case-list")

    def test_returns_tax_cases(self):
        response = self.api_client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data["tax_cases"]),
            1,
        )

        self.assertEqual(
            response.data["tax_cases"][0]["client_name"],
            "Rahul Kumar",
        )