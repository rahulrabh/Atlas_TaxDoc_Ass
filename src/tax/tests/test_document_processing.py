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
from tax.tasks.document_processing import process_document

from tax.services.matching_engine import ( 
    matches_requirement,
)

class DocumentProcessingTests(TestCase):

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

    def create_document(self, file_name, file_hash):
        return Document.objects.create(
            tax_case=self.tax_case,
            file_name=file_name,
            storage_key=f"documents/{file_name}",
            file_hash=file_hash,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

    def test_w2_document_is_classified_and_persisted(self):
        document = self.create_document(
            "rahul_company_a_w2_2025.pdf",
            "a" * 64,
        )

        classification_id = process_document(
            str(document.id)
        )

        classification = DocumentClassification.objects.get(
            id=classification_id
        )

        self.assertEqual(
            classification.document,
            document,
        )

        self.assertEqual(
            classification.document_type,
            RequirementDocumentType.W2,
        )

        self.assertEqual(
            classification.tax_year,
            2025,
        )

        self.assertEqual(
            classification.person,
            self.rahul,
        )

        self.assertEqual(
            classification.employment,
            self.company_a,
        )

        self.assertEqual(
            classification.confidence,
            Decimal("0.9500"),
        )

        self.assertEqual(
            classification.status,
            DocumentClassificationStatus.CLASSIFIED,
        )

        self.assertTrue(
            classification.is_current
        )

    def test_valid_w2_creates_requirement_match(self):
        document = self.create_document(
            "rahul_company_a_w2_2025.pdf",
            "b" * 64,
        )

        process_document(str(document.id))

        classification = DocumentClassification.objects.get(
            document=document,
            is_current=True,
        )

        match = RequirementDocumentMatch.objects.get(
            requirement=self.w2_requirement,
        )

        self.assertEqual(
            match.document,
            document,
        )

        self.assertTrue(
            match.is_active
        )

        self.assertEqual(
            match.status,
            RequirementDocumentMatchStatus.MATCHED,
        )

    def test_unknown_document_is_marked_for_review(self):
        document = self.create_document(
            "unknown_scan.pdf",
            "c" * 64,
        )

        classification_id = process_document(
            str(document.id)
        )

        classification = DocumentClassification.objects.get(
            id=classification_id
        )

        self.assertEqual(
            classification.status,
            DocumentClassificationStatus.REVIEW_REQUIRED,
        )

        self.assertEqual(
            classification.confidence,
            Decimal("0.2000"),
        )

        self.assertEqual(
            classification.document_type,
            RequirementDocumentType.UNKNOWN,
        )

        self.assertFalse(
            RequirementDocumentMatch.objects.exists()
        )

    def test_review_required_document_does_not_create_match(self):
        document = self.create_document(
            "unknown_company_a_w2_2025.pdf",
            "d" * 64,
        )

        process_document(str(document.id))

        self.assertEqual(
            DocumentClassification.objects.count(),
            1,
        )

        self.assertEqual(
            RequirementDocumentMatch.objects.count(),
            0,
        )

    def test_reprocessing_document_preserves_classification_history(self):
        document = self.create_document(
            "rahul_company_a_w2_2025.pdf",
            "e" * 64,
        )

        first_classification_id = process_document(
            str(document.id)
        )

        second_classification_id = process_document(
            str(document.id)
        )

        self.assertNotEqual(
            first_classification_id,
            second_classification_id,
        )

        self.assertEqual(
            DocumentClassification.objects.filter(
                document=document
            ).count(),
            2,
        )

    def test_reprocessing_keeps_only_one_current_classification(self):
        document = self.create_document(
            "rahul_company_a_w2_2025.pdf",
            "f" * 64,
        )

        process_document(str(document.id))
        process_document(str(document.id))

        current_classifications = (
            DocumentClassification.objects.filter(
                document=document,
                is_current=True,
            )
        )

        self.assertEqual(
            current_classifications.count(),
            1,
        )

    def test_previous_classification_becomes_non_current(self):
        document = self.create_document(
            "rahul_company_a_w2_2025.pdf",
            "1" * 64,
        )

        first_classification_id = process_document(
            str(document.id)
        )

        process_document(str(document.id))

        first_classification = (
            DocumentClassification.objects.get(
                id=first_classification_id
            )
        )

        self.assertFalse(
            first_classification.is_current
        )

    def test_form_1040_is_classified_without_person_or_employment(self):
        document = self.create_document(
            "previous_year_1040_2024.pdf",
            "2" * 64,
        )

        classification_id = process_document(
            str(document.id)
        )

        classification = DocumentClassification.objects.get(
            id=classification_id
        )

        self.assertEqual(
            classification.document_type,
            RequirementDocumentType.FORM_1040,
        )

        self.assertEqual(
            classification.tax_year,
            2024,
        )

        self.assertIsNone(
            classification.person
        )

        self.assertIsNone(
            classification.employment
        )

        classification = DocumentClassification.objects.get(
            document=document,
            is_current=True,
        )