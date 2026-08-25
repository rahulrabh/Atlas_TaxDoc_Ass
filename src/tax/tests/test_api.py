from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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


class TaxCaseStatusAPITests(APITestCase):

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

    def get_status_url(self):
        return reverse(
            "tax-case-status",
            kwargs={
                "tax_case_id": self.tax_case.id,
            },
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
    ):
        return DocumentClassification.objects.create(
            document=document,
            document_type=document_type,
            tax_year=tax_year,
            person=person,
            employment=employment,
            confidence=confidence,
            status=status,
            is_current=True,
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

    def test_get_tax_case_status_returns_200(self):
        response = self.client.get(
            self.get_status_url()
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_response_contains_tax_case_information(self):
        response = self.client.get(
            self.get_status_url()
        )

        self.assertEqual(
            response.data["tax_case_id"],
            str(self.tax_case.id),
        )

        self.assertEqual(
            response.data["tax_year"],
            2025,
        )

    def test_initial_requirements_are_outstanding(self):
        response = self.client.get(
            self.get_status_url()
        )

        self.assertEqual(
            response.data["summary"]["total"],
            3,
        )

        self.assertEqual(
            response.data["summary"]["received"],
            0,
        )

        self.assertEqual(
            response.data["summary"]["outstanding"],
            3,
        )

        self.assertEqual(
            response.data["summary"]["needs_review"],
            0,
        )

    def test_matched_requirement_is_returned_as_received(self):
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

        response = self.client.get(
            self.get_status_url()
        )

        self.assertEqual(
            response.data["summary"]["received"],
            1,
        )

        self.assertEqual(
            response.data["summary"]["outstanding"],
            2,
        )

        w2_result = next(
            item
            for item in response.data["requirements"]
            if item["id"] == str(self.w2_requirement.id)
        )

        self.assertEqual(
            w2_result["status"],
            "RECEIVED",
        )

    def test_review_required_document_is_counted(self):
        document = self.create_document(
            "uncertain_document.pdf",
            "b" * 64,
        )

        self.create_classification(
            document=document,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
            person=self.rahul,
            employment=self.company_a,
            confidence=Decimal("0.4000"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
        )

        response = self.client.get(
            self.get_status_url()
        )

        self.assertEqual(
            response.data["summary"]["needs_review"],
            1,
        )

    def test_unknown_tax_case_returns_404(self):
        import uuid

        url = reverse(
            "tax-case-status",
            kwargs={
                "tax_case_id": uuid.uuid4(),
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )