from django.db import IntegrityError
from django.test import TestCase

from tax.models import (
    Client,
    Document,
    DocumentProcessingStatus,
    TaxCase,
)


class DocumentModelTests(TestCase):

    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Acme Corp Client",
        )

        self.tax_case = TaxCase.objects.create(
            client=self.client_obj,
            tax_year=2025,
            filing_status=TaxCase.FilingStatus.MARRIED_JOINTLY,
        )

    def test_can_create_document(self):
        document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_w2_company_a.pdf",
            storage_key="documents/rahul_w2_company_a.pdf",
            file_hash="a" * 64,
        )

        self.assertIsNotNone(document.id)
        self.assertEqual(document.tax_case, self.tax_case)
        self.assertEqual(
            document.file_name,
            "rahul_w2_company_a.pdf",
        )
        self.assertEqual(
            document.storage_key,
            "documents/rahul_w2_company_a.pdf",
        )
        self.assertEqual(
            document.file_hash,
            "a" * 64,
        )

    def test_new_document_starts_as_uploaded(self):
        document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_w2_company_a.pdf",
            storage_key="documents/rahul_w2_company_a.pdf",
            file_hash="b" * 64,
        )

        self.assertEqual(
            document.processing_status,
            DocumentProcessingStatus.UPLOADED,
        )

    def test_duplicate_file_hash_is_rejected(self):
        Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_w2_company_a.pdf",
            storage_key="documents/rahul_w2_company_a.pdf",
            file_hash="c" * 64,
        )

        with self.assertRaises(IntegrityError):
            Document.objects.create(
                tax_case=self.tax_case,
                file_name="same_file_different_name.pdf",
                storage_key="documents/another_file.pdf",
                file_hash="c" * 64,
            )

    def test_different_file_hashes_are_allowed(self):
        first_document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_w2_company_a.pdf",
            storage_key="documents/rahul_w2_company_a.pdf",
            file_hash="d" * 64,
        )

        second_document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_w2_company_b.pdf",
            storage_key="documents/rahul_w2_company_b.pdf",
            file_hash="e" * 64,
        )

        self.assertNotEqual(
            first_document.file_hash,
            second_document.file_hash,
        )

        self.assertEqual(
            Document.objects.filter(
                tax_case=self.tax_case,
            ).count(),
            2,
        )

    def test_document_belongs_to_correct_tax_case(self):
        second_client = Client.objects.create(
            name="Second Client",
        )

        second_tax_case = TaxCase.objects.create(
            client=second_client,
            tax_year=2026,
            filing_status=TaxCase.FilingStatus.SINGLE,
        )

        first_document = Document.objects.create(
            tax_case=self.tax_case,
            file_name="rahul_2025_w2.pdf",
            storage_key="documents/rahul_2025_w2.pdf",
            file_hash="f" * 64,
        )

        second_document = Document.objects.create(
            tax_case=second_tax_case,
            file_name="rahul_2026_w2.pdf",
            storage_key="documents/rahul_2026_w2.pdf",
            file_hash="1" * 64,
        )

        self.assertEqual(
            first_document.tax_case,
            self.tax_case,
        )

        self.assertEqual(
            second_document.tax_case,
            second_tax_case,
        )

        self.assertEqual(
            self.tax_case.documents.count(),
            1,
        )

        self.assertEqual(
            second_tax_case.documents.count(),
            1,
        )