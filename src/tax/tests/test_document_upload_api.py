from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from tax.models import (
    Client,
    Document,
    DocumentProcessingStatus,
    Employment,
    Person,
    TaxCase,
)


class DocumentUploadAPITests(TestCase):

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

        self.url = reverse(
            "document-upload",
            kwargs={"tax_case_id": self.tax_case.id},
        )

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_upload_document_returns_202(
        self,
        mock_delay,
    ):
        uploaded_file = SimpleUploadedFile(
            "rahul_w2.pdf",
            b"test W2 document",
            content_type="application/pdf",
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.api_client.post(
                self.url,
                {"file": uploaded_file},
                format="multipart",
            )

        self.assertEqual(response.status_code, 202)

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        document = Document.objects.first()

        self.assertEqual(
            response.data["id"],
            str(document.id),
        )

        self.assertEqual(
            response.data["status"],
            DocumentProcessingStatus.UPLOADED,
        )

        mock_delay.assert_called_once_with(
            str(document.id),
        )

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_duplicate_document_returns_409(
        self,
        mock_delay,
    ):
        payload = {
            "file": (
                "rahul_w2.pdf",
                b"same document",
                "application/pdf",
            )
        }

        first_response = self.api_client.post(
            self.url,
            payload,
            format="multipart",
        )

        self.assertEqual(
            first_response.status_code,
            202,
        )

        second_response = self.api_client.post(
            self.url,
            payload,
            format="multipart",
        )

        self.assertEqual(
            second_response.status_code,
            409,
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        mock_delay.assert_called_once()

    def test_missing_file_returns_400(self):
        response = self.api_client.post(
            self.url,
            {},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Document.objects.count(),
            0,
        )

    def test_invalid_tax_case_returns_404(self):
        url = reverse(
            "document-upload",
            kwargs={"tax_case_id": "00000000-0000-0000-0000-000000000000"},
        )

        response = self.api_client.post(
            url,
            {
                "file": (
                    "test.pdf",
                    b"document",
                    "application/pdf",
                )
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    @patch(
        "tax.services.document_upload.process_document.delay"
    )
    def test_duplicate_document_returns_409(
        self,
        mock_delay,
    ):
        first_file = SimpleUploadedFile(
            "rahul_w2.pdf",
            b"same document",
            content_type="application/pdf",
        )

        with self.captureOnCommitCallbacks(execute=True):
            first_response = self.api_client.post(
                self.url,
                {"file": first_file},
                format="multipart",
            )

        self.assertEqual(
            first_response.status_code,
            202,
        )

        second_file = SimpleUploadedFile(
            "rahul_w2.pdf",
            b"same document",
            content_type="application/pdf",
        )

        second_response = self.api_client.post(
            self.url,
            {"file": second_file},
            format="multipart",
        )

        self.assertEqual(
            second_response.status_code,
            409,
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        mock_delay.assert_called_once()