from datetime import date

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
    TaxCase,
    RequirementDocumentType,
)


class DocumentReviewAPITests(TestCase):

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

        self.url = reverse(
            "document-review",
            kwargs={
                "tax_case_id": self.tax_case.id,
            },
        )

    def create_review_document(
        self,
        file_name="unknown.pdf",
    ):
        document = Document.objects.create(
            tax_case=self.tax_case,
            file_name=file_name,
            storage_key=f"documents/{file_name}",
            file_hash=file_name + ("a" * (64 - len(file_name))),
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

        return DocumentClassification.objects.create(
            document=document,
            document_type=RequirementDocumentType.UNKNOWN,
            confidence="0.2000",
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
            is_current=True,
        )

    def test_returns_200(self):
        response = self.api_client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_review_required_document_is_returned(self):
        classification = self.create_review_document(
            "unknown.pdf",
        )

        response = self.api_client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data["reviews"]),
            1,
        )

        review = response.data["reviews"][0]

        self.assertEqual(
            review["document_id"],
            str(classification.document.id),
        )

        self.assertEqual(
            review["file_name"],
            "unknown.pdf",
        )

        self.assertEqual(
            review["status"],
            DocumentClassificationStatus.REVIEW_REQUIRED,
        )

    def test_classified_document_is_not_returned(self):
        document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="w2.pdf",
            storage_key="documents/w2.pdf",
            file_hash="b" * 64,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

        DocumentClassification.objects.create(
            document=document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            confidence="0.9500",
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        response = self.api_client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data["reviews"]),
            0,
        )

    def test_invalid_tax_case_returns_404(self):
        url = reverse(
            "document-review",
            kwargs={
                "tax_case_id":
                    "00000000-0000-0000-0000-000000000000",
            },
        )

        response = self.api_client.get(url)

        self.assertEqual(
            response.status_code,
            404,
        )