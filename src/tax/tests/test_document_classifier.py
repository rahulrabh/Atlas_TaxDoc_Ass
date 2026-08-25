from datetime import date
from decimal import Decimal

from django.test import TestCase

from tax.models import (
    Client,
    Document,
    DocumentClassificationStatus,
    DocumentProcessingStatus,
    Employment,
    Person,
    RequirementDocumentType,
    TaxCase,
)

from tax.services.document_classifier import DocumentClassifier


class DocumentClassifierTests(TestCase):

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

        self.classifier = DocumentClassifier()

    def create_document(self, file_name, file_hash):
        return Document.objects.create(
            tax_case=self.tax_case,
            file_name=file_name,
            storage_key=f"documents/{file_name}",
            file_hash=file_hash,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

    def test_classifies_w2(self):
        document = self.create_document(
            "rahul_company_a_w2_2025.pdf",
            "a" * 64,
        )

        result = self.classifier.classify(document)

        self.assertEqual(
            result.document_type,
            RequirementDocumentType.W2,
        )

        self.assertEqual(
            result.tax_year,
            2025,
        )

        self.assertEqual(
            result.person_id,
            self.rahul.id,
        )

        self.assertEqual(
            result.employment_id,
            self.company_a.id,
        )

        self.assertEqual(
            result.confidence,
            Decimal("0.9500"),
        )

        self.assertEqual(
            result.status,
            DocumentClassificationStatus.CLASSIFIED,
        )

    def test_classifies_previous_year_1040(self):
        document = self.create_document(
            "previous_year_1040_2024.pdf",
            "b" * 64,
        )

        result = self.classifier.classify(document)

        self.assertEqual(
            result.document_type,
            RequirementDocumentType.FORM_1040,
        )

        self.assertEqual(
            result.tax_year,
            2024,
        )

        self.assertIsNone(
            result.person_id,
        )

        self.assertIsNone(
            result.employment_id,
        )

    def test_classifies_government_id(self):
        document = self.create_document(
            "rahul_government_id_2025.pdf",
            "c" * 64,
        )

        result = self.classifier.classify(document)

        self.assertEqual(
            result.document_type,
            RequirementDocumentType.GOVERNMENT_ID,
        )

        self.assertEqual(
            result.person_id,
            self.rahul.id,
        )

        self.assertIsNone(
            result.employment_id,
        )

    def test_unknown_document_requires_review(self):
        document = self.create_document(
            "unknown_scan.pdf",
            "d" * 64,
        )

        result = self.classifier.classify(document)

        self.assertEqual(
            result.status,
            DocumentClassificationStatus.REVIEW_REQUIRED,
        )

        self.assertEqual(
            result.confidence,
            Decimal("0.2000"),
        )

        self.assertEqual(
            result.document_type,
            RequirementDocumentType.UNKNOWN,
        )

    def test_unreadable_document_requires_review(self):
        document = self.create_document(
            "unreadable_scan.pdf",
            "e" * 64,
        )

        result = self.classifier.classify(document)

        self.assertEqual(
            result.status,
            DocumentClassificationStatus.REVIEW_REQUIRED,
        )

    def test_unknown_person_w2_requires_review(self):
        document = self.create_document(
            "gaurav_company_a_w2_2025.pdf",
            "f" * 64,
        )

        result = self.classifier.classify(document)

        self.assertEqual(
            result.status,
            DocumentClassificationStatus.REVIEW_REQUIRED,
        )

    def test_unknown_document_type_requires_review(self):
        document = self.create_document(
            "random_file_2025.pdf",
            "1" * 64,
        )

        result = self.classifier.classify(document)

        self.assertEqual(
            result.status,
            DocumentClassificationStatus.REVIEW_REQUIRED,
        )