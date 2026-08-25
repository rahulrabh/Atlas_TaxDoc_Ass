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
from tax.services.collection_status import get_collection_status


class CollectionStatusTests(TestCase):

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

        self.priya = Person.objects.create(
            tax_case=self.tax_case,
            name="Priya",
            role=Person.Role.SPOUSE,
        )

        self.company_a = Employment.objects.create(
            person=self.rahul,
            employer_name="Company A",
            start_date=date(2025, 1, 1),
        )

        self.company_b = Employment.objects.create(
            person=self.rahul,
            employer_name="Company B",
            start_date=date(2025, 6, 1),
        )

        self.w2_requirement = Requirement.objects.create(
            tax_case=self.tax_case,
            person=self.rahul,
            employment=self.company_a,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
        )

        self.gov_id_requirement = Requirement.objects.create(
            tax_case=self.tax_case,
            person=self.rahul,
            employment=None,
            document_type=RequirementDocumentType.GOVERNMENT_ID,
            tax_year=2025,
        )

        self.form_1040_requirement = Requirement.objects.create(
            tax_case=self.tax_case,
            person=None,
            employment=None,
            document_type=RequirementDocumentType.FORM_1040,
            tax_year=2024,
        )

    def create_document(self, file_name, file_hash):
        return Document.objects.create(
            tax_case=self.tax_case,
            file_name=file_name,
            storage_key=f"documents/{file_name}",
            file_hash=file_hash,
            processing_status=DocumentProcessingStatus.PROCESSED,
        )

    def create_classification(
        self,
        document,
        document_type,
        tax_year,
        person=None,
        employment=None,
        confidence=Decimal("0.9500"),
        status=DocumentClassificationStatus.CLASSIFIED,
        is_current=True,
    ):
        return DocumentClassification.objects.create(
            document=document,
            document_type=document_type,
            tax_year=tax_year,
            person=person,
            employment=employment,
            confidence=confidence,
            status=status,
            is_current=is_current,
        )

    def create_match(
        self,
        requirement,
        document,
        classification,
    ):
        return RequirementDocumentMatch.objects.create(
            requirement=requirement,
            document=document,
            classification=classification,
            status=RequirementDocumentMatchStatus.MATCHED,
            is_active=True,
        )

    def test_all_requirements_are_outstanding_initially(self):
        result = get_collection_status(self.tax_case)

        self.assertEqual(
            result["summary"]["total"],
            3,
        )

        self.assertEqual(
            result["summary"]["received"],
            0,
        )

        self.assertEqual(
            result["summary"]["outstanding"],
            3,
        )

        self.assertEqual(
            result["summary"]["needs_review"],
            0,
        )

        for item in result["requirements"]:
            self.assertEqual(
                item["status"],
                "OUTSTANDING",
            )
            self.assertIsNone(item["match"])

    def test_matched_requirement_becomes_received(self):
        document = self.create_document(
            "rahul_company_a_w2.pdf",
            "a" * 64,
        )

        classification = self.create_classification(
            document=document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
        )

        self.create_match(
            requirement=self.w2_requirement,
            document=document,
            classification=classification,
        )

        result = get_collection_status(self.tax_case)

        w2_result = next(
            item
            for item in result["requirements"]
            if item["requirement"].id == self.w2_requirement.id
        )

        self.assertEqual(
            w2_result["status"],
            "RECEIVED",
        )

        self.assertIsNotNone(
            w2_result["match"],
        )

    def test_unmatched_requirement_remains_outstanding(self):
        document = self.create_document(
            "rahul_company_a_w2.pdf",
            "b" * 64,
        )

        # The document exists, but no valid match exists.
        self.create_classification(
            document=document,
            document_type=RequirementDocumentType.W2,
            tax_year=2024,
            person=self.rahul,
            employment=self.company_a,
        )

        result = get_collection_status(self.tax_case)

        w2_result = next(
            item
            for item in result["requirements"]
            if item["requirement"].id == self.w2_requirement.id
        )

        self.assertEqual(
            w2_result["status"],
            "OUTSTANDING",
        )

        self.assertIsNone(
            w2_result["match"],
        )

    def test_review_required_classification_appears_in_reviews(self):
        document = self.create_document(
            "uncertain_w2.pdf",
            "c" * 64,
        )

        classification = self.create_classification(
            document=document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
            confidence=Decimal("0.4500"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
        )

        result = get_collection_status(self.tax_case)

        self.assertEqual(
            result["summary"]["needs_review"],
            1,
        )

        review = result["reviews"].first()

        self.assertEqual(
            review.id,
            classification.id,
        )

    def test_received_requirement_remains_received_when_another_document_needs_review(
        self,
    ):
        # Valid document that satisfies the requirement.
        valid_document = self.create_document(
            "rahul_company_a_w2.pdf",
            "d" * 64,
        )

        valid_classification = self.create_classification(
            document=valid_document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
        )

        self.create_match(
            requirement=self.w2_requirement,
            document=valid_document,
            classification=valid_classification,
        )

        # Separate uncertain document.
        review_document = self.create_document(
            "uncertain_document.pdf",
            "e" * 64,
        )

        self.create_classification(
            document=review_document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_b,
            confidence=Decimal("0.4000"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
        )

        result = get_collection_status(self.tax_case)

        self.assertEqual(
            result["summary"]["received"],
            1,
        )

        self.assertEqual(
            result["summary"]["outstanding"],
            2,
        )

        self.assertEqual(
            result["summary"]["needs_review"],
            1,
        )

        w2_result = next(
            item
            for item in result["requirements"]
            if item["requirement"].id == self.w2_requirement.id
        )

        self.assertEqual(
            w2_result["status"],
            "RECEIVED",
        )

    def test_summary_counts_are_correct(self):
        document = self.create_document(
            "rahul_company_a_w2.pdf",
            "f" * 64,
        )

        classification = self.create_classification(
            document=document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
        )

        self.create_match(
            requirement=self.w2_requirement,
            document=document,
            classification=classification,
        )

        review_document = self.create_document(
            "review.pdf",
            "1" * 64,
        )

        self.create_classification(
            document=review_document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_b,
            confidence=Decimal("0.3000"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
        )

        result = get_collection_status(self.tax_case)

        self.assertEqual(
            result["summary"],
            {
                "total": 3,
                "received": 1,
                "outstanding": 2,
                "needs_review": 1,
            },
        )