from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .base import BaseModel
from .document import Document
from .employment import Employment
from .person import Person
from .requirements import RequirementDocumentType


class DocumentClassificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CLASSIFIED = "CLASSIFIED", "Classified"
    REVIEW_REQUIRED = "REVIEW_REQUIRED", "Review Required"
    FAILED = "FAILED", "Failed"


class DocumentClassification(BaseModel):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="classifications",
    )

    document_type = models.CharField(
        max_length=30,
        choices=RequirementDocumentType.choices,
    )

    tax_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_classifications",
    )

    employment = models.ForeignKey(
        Employment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_classifications",
    )

    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1),
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=DocumentClassificationStatus.choices,
        default=DocumentClassificationStatus.PENDING,
    )

    is_current = models.BooleanField(
        default=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document"],
                condition=models.Q(is_current=True),
                name="unique_current_classification_per_document",
            ),
        ]