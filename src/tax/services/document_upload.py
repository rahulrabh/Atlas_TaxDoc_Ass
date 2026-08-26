import hashlib

from django.db import transaction

from tax.models import Document, DocumentProcessingStatus
from tax.tasks.document_processing import process_document

from tax.services.document_storage import save_document_file

class DuplicateDocumentError(Exception):
    pass


def calculate_file_hash(uploaded_file):
    """
    Calculate the SHA-256 hash of an uploaded file.
    """

    sha256 = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        sha256.update(chunk)

    uploaded_file.seek(0)

    return sha256.hexdigest()


@transaction.atomic
def upload_document(tax_case, uploaded_file):
    """
    Create a document record and enqueue asynchronous processing.
    """

    file_hash = calculate_file_hash(uploaded_file)

    existing_document = Document.objects.filter(
        file_hash=file_hash,
    ).first()

    if existing_document:
        raise DuplicateDocumentError()

    document = Document(
        tax_case=tax_case,
        file_name=uploaded_file.name,
        file_hash=file_hash,
        processing_status=DocumentProcessingStatus.UPLOADED,
    )

    document.save()

    document.storage_key = (
        f"documents/{document.id}/{uploaded_file.name}"
    )

    storage_key = save_document_file(
        uploaded_file=uploaded_file,
        document_id=document.id,
        file_name=uploaded_file.name,
    )

    document.storage_key = storage_key

    document.save(
        update_fields=["storage_key"]
    )

    transaction.on_commit(
        lambda: process_document.delay(str(document.id))
    )

    return document