from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from tax.models import (
    Client,
    Document,
    DocumentClassification,
    DocumentClassificationStatus,
    DocumentProcessingStatus,
    Employment,
    Person,
    Requirement,
    RequirementDocumentMatch,
    RequirementDocumentType,
    TaxCase,
)


class DocumentReviewResolutionAPITests(TestCase):

    def setUp(self):
        self.api_client = APIClient()

        client = Client.objects.create(
            name="Acme Corp Client",
        )

        self.tax_case = TaxCase.objects.create(
            client=client,
            tax_year=2025,
            filing_status=TaxCase.FilingStatus.MARRIED_JOINTLY,
        )

        self.person = Person.objects.create(
            tax_case=self.tax_case,
            name="Rahul",
            role=Person.Role.TAXPAYER,
        )

        self.employment = Employment.objects.create(
            person=self.person,
            employer_name="Company A",
            start_date=date(2025, 1, 1),
        )

        self.requirement = Requirement.objects.create(
            tax_case=self.tax_case,
            person=self.person,
            employment=self.employment,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
        )

        self.document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="unknown_w2.pdf",
            storage_key="documents/unknown_w2.pdf",
            file_hash="a" * 64,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

        self.classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.UNKNOWN,
            confidence=Decimal("0.2000"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
            is_current=True,
            person=self.person,
            employment=self.employment,
        )

        self.url = reverse(
            "document-review-resolution",
            kwargs={
                "document_id": self.document.id,
            },
        )

    def test_resolve_review_returns_200(self):
        response = self.api_client.patch(
            self.url,
            {
                "document_type": RequirementDocumentType.W2,
                "tax_year": 2025,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_resolution_preserves_old_classification(self):
        response = self.api_client.patch(
            self.url,
            {
                "document_type": RequirementDocumentType.W2,
                "tax_year": 2025,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.classification.refresh_from_db()

        self.assertFalse(
            self.classification.is_current
        )

        self.assertEqual(
            DocumentClassification.objects.filter(
                document=self.document
            ).count(),
            2,
        )

    def test_resolution_creates_active_match(self):
        response = self.api_client.patch(
            self.url,
            {
                "document_type": RequirementDocumentType.W2,
                "tax_year": 2025,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        match = RequirementDocumentMatch.objects.get(
            requirement=self.requirement,
            is_active=True,
        )

        self.assertEqual(
            match.document,
            self.document,
        )