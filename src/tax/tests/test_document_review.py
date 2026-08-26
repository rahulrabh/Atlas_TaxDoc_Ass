from datetime import date
from decimal import Decimal

from django.test import TestCase

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
    RequirementDocumentMatchStatus,
    RequirementDocumentType,
    TaxCase,
)

from tax.services.document_review import (
    resolve_document_review,
)


class DocumentReviewTests(TestCase):

    def setUp(self):
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

    def create_review_classification(self):
        document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="unknown_company_a_w2_2025.pdf",
            storage_key="documents/unknown_company_a_w2_2025.pdf",
            file_hash="a" * 64,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

        return DocumentClassification.objects.create(
            document=document,
            document_type=RequirementDocumentType.UNKNOWN,
            tax_year=None,
            person=self.rahul,
            employment=self.company_a,
            confidence=Decimal("0.2000"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
            is_current=True,
        )

    def test_resolve_review_creates_new_classification(self):
        classification = self.create_review_classification()

        new_classification = resolve_document_review(
            classification=classification,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
        )

        self.assertIsNotNone(
            new_classification
        )

        self.assertEqual(
            new_classification.document_type,
            RequirementDocumentType.W2,
        )

        self.assertEqual(
            new_classification.tax_year,
            2025,
        )

        self.assertEqual(
            new_classification.confidence,
            Decimal("1.0000"),
        )

        self.assertEqual(
            new_classification.status,
            DocumentClassificationStatus.CLASSIFIED,
        )

        self.assertTrue(
            new_classification.is_current
        )

    def test_resolve_review_preserves_history(self):
        classification = self.create_review_classification()

        new_classification = resolve_document_review(
            classification=classification,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
        )

        self.assertEqual(
            DocumentClassification.objects.filter(
                document=classification.document
            ).count(),
            2,
        )

        classification.refresh_from_db()

        self.assertFalse(
            classification.is_current
        )

        self.assertTrue(
            new_classification.is_current
        )

    def test_resolve_review_creates_match(self):
        classification = self.create_review_classification()

        new_classification = resolve_document_review(
            classification=classification,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
        )

        match = RequirementDocumentMatch.objects.get(
            requirement=self.w2_requirement,
            is_active=True,
        )

        self.assertEqual(
            match.classification,
            new_classification,
        )

        self.assertEqual(
            match.status,
            RequirementDocumentMatchStatus.MATCHED,
        )