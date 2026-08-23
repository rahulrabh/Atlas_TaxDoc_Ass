from .base import BaseModel
from .tax_case import TaxCase

from django.db import models

class DocumentProcessingStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    PROCESSING = "PROCESSING", "Processing"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"

class Document(BaseModel):
    tax_case = models.ForeignKey(
        TaxCase,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    file_name = models.CharField(
        max_length=255,
    )

    storage_key = models.CharField(
        max_length=500,
    )

    file_hash = models.CharField(
        max_length=64,
        unique=True,
    )

    processing_status = models.CharField(
        max_length=20,
        choices=DocumentProcessingStatus.choices,
        default=DocumentProcessingStatus.UPLOADED,
    )