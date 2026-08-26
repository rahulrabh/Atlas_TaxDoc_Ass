from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from tax.models import (
    Client,
    Employment,
    Person,
    Requirement,
    RequirementDocumentType,
    TaxCase,
    Client,
    Document,
    DocumentClassification,
    DocumentClassificationStatus,
    DocumentClassificationStatus,
    DocumentProcessingStatus,
    DocumentClassification,
    RequirementDocumentMatch,
    RequirementDocumentMatchStatus,
)


class CollectionStatusAPITests(TestCase):

    def setUp(self):
        self.api_client = APIClient()

        self.client_obj = Client.objects.create(
            name="Acme Corp Client",
        )

        self.tax_case = TaxCase.objects.create(
            client=self.client_obj,
            tax_year=2025,
            filing_status=TaxCase.FilingStatus.MARRIED_JOINTLY,
        )

        self.rahul = Person.objects.create(
            tax_case=self.tax_case,
            name="Rahul",
            role=Person.Role.TAXPAYER,
        )

        self.company_a = Employment.objects.create(
            person=self.rahul,
            employer_name="Company A",
            start_date=date(2025, 1, 1),
        )

        self.w2_requirement = Requirement.objects.create(
            tax_case=self.tax_case,
            person=self.rahul,
            employment=self.company_a,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
        )

        self.url = reverse(
            "collection-status",
            kwargs={"tax_case_id": self.tax_case.id},
        )

    def test_collection_status_returns_200(self):
        response = self.api_client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_outstanding_requirement_is_returned(self):
        response = self.api_client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data["requirements"]),
            1,
        )

        requirement = response.data["requirements"][0]

        self.assertEqual(
            requirement["requirement_id"],
            str(self.w2_requirement.id),
        )

        self.assertEqual(
            requirement["document_type"],
            RequirementDocumentType.W2,
        )

        self.assertEqual(
            requirement["status"],
            "OUTSTANDING",
        )

    def test_received_requirement_is_returned(self):
        document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_w2.pdf",
            storage_key="documents/rahul_w2.pdf",
            file_hash="a" * 64,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

        classification = DocumentClassification.objects.create(
            document=document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
            confidence="0.9500",
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        RequirementDocumentMatch.objects.create(
            requirement=self.w2_requirement,
            document=document,
            classification=classification,
            status=RequirementDocumentMatchStatus.MATCHED,
            is_active=True,
            match_reason="Test match",
        )

        response = self.api_client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        requirement = response.data["requirements"][0]

        self.assertEqual(
            requirement["requirement_id"],
            str(self.w2_requirement.id),
        )

        self.assertEqual(
            requirement["status"],
            "RECEIVED",
        )

    def test_invalid_tax_case_returns_404(self):
        url = reverse(
            "collection-status",
            kwargs={
                "tax_case_id":
                    "00000000-0000-0000-0000-000000000000"
            },
        )

        response = self.api_client.get(url)

        self.assertEqual(
            response.status_code,
            404,
        )