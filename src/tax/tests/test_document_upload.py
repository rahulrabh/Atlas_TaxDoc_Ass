from datetime import date
from io import BytesIO
from unittest.mock import patch
import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from unittest.mock import patch

from tax.models import (
    Client,
    Document,
    DocumentProcessingStatus,
    Employment,
    Person,
    Requirement,
    RequirementDocumentType,
    TaxCase,
)

from tax.services.document_upload import (
    DuplicateDocumentError,
    calculate_file_hash,
    upload_document,
)


class DocumentUploadServiceTests(TestCase):

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

    def create_uploaded_file(
        self,
        name="rahul_w2.pdf",
        content=b"fake W2 document",
    ):
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type="application/pdf",
        )

    def test_calculates_sha256_hash(self):
        uploaded_file = self.create_uploaded_file(
            content=b"hello world",
        )

        file_hash = calculate_file_hash(uploaded_file)

        self.assertEqual(
            file_hash,
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
        )

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_upload_creates_document(self, mock_delay):
        uploaded_file = self.create_uploaded_file()

        document = upload_document(
            tax_case=self.tax_case,
            uploaded_file=uploaded_file,
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        self.assertEqual(
            document.tax_case,
            self.tax_case,
        )

        self.assertEqual(
            document.file_name,
            "rahul_w2.pdf",
        )

        self.assertEqual(
            document.processing_status,
            DocumentProcessingStatus.UPLOADED,
        )

        self.assertEqual(
            len(document.file_hash),
            64,
        )

        self.assertTrue(
            document.storage_key,
        )

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_upload_queues_processing_task(
        self,
        mock_delay,
    ):
        uploaded_file = self.create_uploaded_file()

        with self.captureOnCommitCallbacks(execute=True):
            document = upload_document(
                tax_case=self.tax_case,
                uploaded_file=uploaded_file,
            )

        mock_delay.assert_called_once_with(
            str(document.id),
        )

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_duplicate_file_is_rejected(
        self,
        mock_delay,
    ):
        first_file = self.create_uploaded_file(
            content=b"same document",
        )

        upload_document(
            tax_case=self.tax_case,
            uploaded_file=first_file,
        )

        second_file = self.create_uploaded_file(
            name="different_name.pdf",
            content=b"same document",
        )

        with self.assertRaises(
            DuplicateDocumentError
        ):
            upload_document(
                tax_case=self.tax_case,
                uploaded_file=second_file,
            )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

    @patch(
    "tax.services.document_upload.process_document.delay"
    )
    def test_duplicate_file_does_not_queue_second_task(
        self,
        mock_delay,
    ):
        first_file = self.create_uploaded_file(
            content=b"same document",
        )

        with self.captureOnCommitCallbacks(execute=True):
            upload_document(
                tax_case=self.tax_case,
                uploaded_file=first_file,
            )

        second_file = self.create_uploaded_file(
            content=b"same document",
        )

        with self.assertRaises(DuplicateDocumentError):
            upload_document(
                tax_case=self.tax_case,
                uploaded_file=second_file,
            )

        mock_delay.assert_called_once()

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_storage_key_contains_document_id_and_filename(
        self,
        mock_delay,
    ):
        uploaded_file = self.create_uploaded_file(
            name="rahul_w2.pdf",
        )

        document = upload_document(
            tax_case=self.tax_case,
            uploaded_file=uploaded_file,
        )

        self.assertEqual(
            document.storage_key,
            f"documents/{document.id}/rahul_w2.pdf",
        )

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_upload_physically_stores_file(
        self,
        mock_delay,
    ):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):

                uploaded_file = self.create_uploaded_file(
                    name="rahul_w2.pdf",
                    content=b"real tax document",
                )

                document = upload_document(
                    tax_case=self.tax_case,
                    uploaded_file=uploaded_file,
                )

                file_path = os.path.join(
                    media_root,
                    document.storage_key,
                )

                self.assertTrue(
                    os.path.exists(file_path)
                )

                with open(file_path, "rb") as stored_file:
                    self.assertEqual(
                        stored_file.read(),
                        b"real tax document",
                    )    

    @patch(
        "tax.services.document_upload.save_document_file"
    )
    def test_storage_failure_rolls_back_document(
        self,
        mock_save,
    ):
        mock_save.side_effect = OSError(
            "Storage failed"
        )

        uploaded_file = self.create_uploaded_file()

        with self.assertRaises(OSError):
            upload_document(
                tax_case=self.tax_case,
                uploaded_file=uploaded_file,
            )

        self.assertEqual(
            Document.objects.count(),
            0,
        )