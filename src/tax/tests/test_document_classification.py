from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from tax.models import (
    Client,
    Document,
    DocumentClassification,
    DocumentClassificationStatus,
    DocumentProcessingStatus,
    Employment,
    Person,
    RequirementDocumentType,
    TaxCase,
)


class DocumentClassificationTests(TestCase):

    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Acme Corp Client",
        )

        self.tax_case = TaxCase.objects.create(
            client=self.client_obj,
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

        self.document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_w2.pdf",
            storage_key="documents/rahul_w2.pdf",
            file_hash="a" * 64,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

    def test_can_create_classification(self):
        classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.person,
            employment=self.employment,
            confidence=Decimal("0.9500"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        self.assertIsNotNone(classification.id)
        self.assertEqual(
            classification.document,
            self.document,
        )
        self.assertEqual(
            classification.person,
            self.person,
        )
        self.assertEqual(
            classification.employment,
            self.employment,
        )
        self.assertEqual(
            classification.confidence,
            Decimal("0.9500"),
        )

    def test_classification_defaults_to_pending(self):
        classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
        )

        self.assertEqual(
            classification.status,
            DocumentClassificationStatus.PENDING,
        )

    def test_classification_defaults_to_not_current(self):
        classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
        )

        self.assertFalse(classification.is_current)

    def test_person_and_employment_can_be_null(self):
        classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.FORM_1040,
            tax_year=2024,
            confidence=Decimal("0.9000"),
        )

        self.assertIsNone(classification.person)
        self.assertIsNone(classification.employment)

    def test_tax_year_can_be_null(self):
        classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            tax_year=None,
            confidence=Decimal("0.5000"),
        )

        self.assertIsNone(classification.tax_year)

    def test_confidence_accepts_zero(self):
        classification = DocumentClassification(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("0.0000"),
        )

        classification.full_clean()

        self.assertEqual(
            classification.confidence,
            Decimal("0.0000"),
        )

    def test_confidence_accepts_one(self):
        classification = DocumentClassification(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("1.0000"),
        )

        classification.full_clean()

        self.assertEqual(
            classification.confidence,
            Decimal("1.0000"),
        )

    def test_confidence_cannot_exceed_one(self):
        classification = DocumentClassification(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("1.0001"),
        )

        with self.assertRaises(ValidationError):
            classification.full_clean()

    def test_confidence_cannot_be_negative(self):
        classification = DocumentClassification(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("-0.0001"),
        )

        with self.assertRaises(ValidationError):
            classification.full_clean()

    def test_multiple_historical_classifications_are_allowed(self):
        first = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("0.6000"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
            is_current=False,
        )

        second = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("0.9500"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        self.assertEqual(
            DocumentClassification.objects.filter(
                document=self.document,
            ).count(),
            2,
        )

        self.assertFalse(first.is_current)
        self.assertTrue(second.is_current)

    def test_only_one_current_classification_allowed_per_document(self):
        DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("0.9000"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        with self.assertRaises(IntegrityError):
            DocumentClassification.objects.create(
                document=self.document,
                document_type=RequirementDocumentType.W2,
                confidence=Decimal("0.9500"),
                status=DocumentClassificationStatus.CLASSIFIED,
                is_current=True,
            )

    def test_different_documents_can_each_have_current_classification(self):
        second_document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_id.pdf",
            storage_key="documents/rahul_id.pdf",
            file_hash="b" * 64,
        )

        first_classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            confidence=Decimal("0.9500"),
            is_current=True,
        )

        second_classification = DocumentClassification.objects.create(
            document=second_document,
            document_type=RequirementDocumentType.GOVERNMENT_ID,
            confidence=Decimal("0.9800"),
            is_current=True,
        )

        self.assertTrue(first_classification.is_current)
        self.assertTrue(second_classification.is_current)