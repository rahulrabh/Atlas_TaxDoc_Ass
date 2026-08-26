import os
import shutil
import tempfile
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from tax.services.document_storage import (
    delete_document_file,
    save_document_file,
)


class DocumentStorageTests(TestCase):

    def setUp(self):
        self.media_root = tempfile.mkdtemp()

        self.override = override_settings(
            MEDIA_ROOT=self.media_root
        )
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(
            self.media_root,
            ignore_errors=True,
        )

    def test_save_document_file_creates_file(self):
        document_id = uuid4()

        uploaded_file = SimpleUploadedFile(
            "test.pdf",
            b"test document content",
            content_type="application/pdf",
        )

        storage_key = save_document_file(
            uploaded_file=uploaded_file,
            document_id=document_id,
            file_name="test.pdf",
        )

        expected_path = os.path.join(
            self.media_root,
            "documents",
            str(document_id),
            "test.pdf",
        )

        self.assertEqual(
            storage_key,
            f"documents/{document_id}/test.pdf",
        )

        self.assertTrue(
            os.path.exists(expected_path)
        )

    def test_saved_file_contains_original_content(self):
        document_id = uuid4()

        content = b"important tax document"

        uploaded_file = SimpleUploadedFile(
            "tax.pdf",
            content,
            content_type="application/pdf",
        )

        storage_key = save_document_file(
            uploaded_file=uploaded_file,
            document_id=document_id,
            file_name="tax.pdf",
        )

        file_path = os.path.join(
            self.media_root,
            storage_key,
        )

        with open(file_path, "rb") as stored_file:
            self.assertEqual(
                stored_file.read(),
                content,
            )

    def test_delete_document_file_removes_file(self):
        document_id = uuid4()

        uploaded_file = SimpleUploadedFile(
            "delete_me.pdf",
            b"temporary document",
            content_type="application/pdf",
        )

        storage_key = save_document_file(
            uploaded_file=uploaded_file,
            document_id=document_id,
            file_name="delete_me.pdf",
        )

        file_path = os.path.join(
            self.media_root,
            storage_key,
        )

        self.assertTrue(
            os.path.exists(file_path)
        )

        delete_document_file(storage_key)

        self.assertFalse(
            os.path.exists(file_path)
        )

    def test_delete_nonexistent_file_does_not_fail(self):
        delete_document_file(
            "documents/nonexistent/file.pdf"
        )