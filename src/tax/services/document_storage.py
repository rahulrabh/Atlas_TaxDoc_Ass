import os

from django.conf import settings


def save_document_file(uploaded_file, document_id, file_name):
    """
    Save an uploaded document to local filesystem storage.

    Returns the relative storage key.
    """

    relative_path = os.path.join(
        "documents",
        str(document_id),
        file_name,
    )

    absolute_path = os.path.join(
        settings.MEDIA_ROOT,
        relative_path,
    )

    os.makedirs(
        os.path.dirname(absolute_path),
        exist_ok=True,
    )

    with open(absolute_path, "wb") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    uploaded_file.seek(0)

    return relative_path


def delete_document_file(storage_key):
    """
    Delete a stored document file if it exists.
    """

    absolute_path = os.path.join(
        settings.MEDIA_ROOT,
        storage_key,
    )

    if os.path.exists(absolute_path):
        os.remove(absolute_path)