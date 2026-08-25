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
    RequirementDocumentType,
    TaxCase,
    RequirementDocumentMatch,
    RequirementDocumentMatchStatus,
)
from tax.services.matching_engine import ( 
    match_classification_to_requirement,
    matches_requirement,
)

class MatchingEngineTests(TestCase):

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

        self.document = self.create_document(
            "rahul_company_a_w2.pdf",
            "a" * 64,
        )

        self.classification = DocumentClassification.objects.create(
            document=self.document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
            confidence=Decimal("0.9500"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        self.requirement = Requirement.objects.create(
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

    def test_correct_classification_matches_requirement(self):
        self.assertTrue(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_wrong_document_type_does_not_match(self):
        self.requirement.document_type = (
            RequirementDocumentType.GOVERNMENT_ID
        )

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_wrong_tax_year_does_not_match(self):
        self.requirement.tax_year = 2024

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_wrong_person_does_not_match(self):
        self.requirement.person = self.priya

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_wrong_employment_does_not_match(self):
        self.requirement.employment = self.company_b

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_non_current_classification_does_not_match(self):
        self.classification.is_current = False

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_low_confidence_classification_does_not_match(self):
        self.classification.confidence = Decimal("0.7999")

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_exact_threshold_confidence_matches(self):
        self.classification.confidence = Decimal("0.8000")

        self.assertTrue(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_pending_classification_does_not_match(self):
        self.classification.status = (
            DocumentClassificationStatus.PENDING
        )

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_review_required_classification_does_not_match(self):
        self.classification.status = (
            DocumentClassificationStatus.REVIEW_REQUIRED
        )

        self.assertFalse(
            matches_requirement(
                self.classification,
                self.requirement,
            )
        )

    def test_tax_case_level_requirement_can_match(self):
        requirement = Requirement.objects.create(
            tax_case=self.tax_case,
            person=None,
            employment=None,
            document_type=RequirementDocumentType.FORM_1040,
            tax_year=2024,
        )

        document = self.create_document(
            "previous_year_1040.pdf",
            "b" * 64,
        )

        classification = DocumentClassification.objects.create(
            document=document,
            document_type=RequirementDocumentType.FORM_1040,
            tax_year=2024,
            person=None,
            employment=None,
            confidence=Decimal("0.9500"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        self.assertTrue(
            matches_requirement(
                classification,
                requirement,
            )
        )

    def test_person_level_requirement_can_match(self):
        requirement = Requirement.objects.create(
            tax_case=self.tax_case,
            person=self.rahul,
            employment=None,
            document_type=RequirementDocumentType.GOVERNMENT_ID,
            tax_year=2025,
        )

        document = self.create_document(
            "rahul_government_id.pdf",
            "c" * 64,
        )

        classification = DocumentClassification.objects.create(
            document=document,
            document_type=RequirementDocumentType.GOVERNMENT_ID,
            tax_year=2025,
            person=self.rahul,
            employment=None,
            confidence=Decimal("0.9500"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        self.assertTrue(
            matches_requirement(
                classification,
                requirement,
            )
        )

    def test_matching_service_creates_active_match(self):
        match = match_classification_to_requirement(
            self.classification,
            self.requirement,
        )

        self.assertIsNotNone(match)
        self.assertEqual(
            match.requirement,
            self.requirement,
        )
        self.assertEqual(
            match.document,
            self.document,
        )
        self.assertEqual(
            match.classification,
            self.classification,
        )
        self.assertEqual(
            match.status,
            RequirementDocumentMatchStatus.MATCHED,
        )
        self.assertTrue(match.is_active)

    def test_invalid_classification_does_not_create_match(self):
        self.classification.confidence = Decimal("0.5000")
        self.classification.save()

        result = match_classification_to_requirement(
            self.classification,
            self.requirement,
        )

        self.assertIsNone(result)

        self.assertEqual(
            RequirementDocumentMatch.objects.count(),
            0,
        )

    def test_new_valid_match_supersedes_previous_active_match(self):
        first_match = match_classification_to_requirement(
            self.classification,
            self.requirement,
        )

        second_document = self.create_document(
            "rahul_company_a_w2_rescan.pdf",
            "d" * 64,
        )

        second_classification = DocumentClassification.objects.create(
            document=second_document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
            confidence=Decimal("0.9800"),
            status=DocumentClassificationStatus.CLASSIFIED,
            is_current=True,
        )

        second_match = match_classification_to_requirement(
            second_classification,
            self.requirement,
        )

        first_match.refresh_from_db()

        self.assertFalse(first_match.is_active)
        self.assertEqual(
            first_match.status,
            RequirementDocumentMatchStatus.SUPERSEDED,
        )

        self.assertTrue(second_match.is_active)
        self.assertEqual(
            second_match.status,
            RequirementDocumentMatchStatus.MATCHED,
        )

        self.assertEqual(
            RequirementDocumentMatch.objects.filter(
                requirement=self.requirement,
                is_active=True,
            ).count(),
            1,
        )