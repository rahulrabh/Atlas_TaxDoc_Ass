from django.db import models

from .base import BaseModel
from .document import Document
from .document_classification import DocumentClassification
from .requirements import Requirement


class RequirementDocumentMatchStatus(models.TextChoices):
    MATCHED = "MATCHED", "Matched"
    REVIEW_REQUIRED = "REVIEW_REQUIRED", "Review Required"
    REJECTED = "REJECTED", "Rejected"
    SUPERSEDED = "SUPERSEDED", "Superseded" 


class RequirementDocumentMatch(BaseModel):
    requirement = models.ForeignKey(
        Requirement,
        on_delete=models.CASCADE,
        related_name="document_matches",
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="requirement_matches",
    )

    classification = models.ForeignKey(
        DocumentClassification,
        on_delete=models.CASCADE,
        related_name="requirement_matches",
    )

    status = models.CharField(
        max_length=20,
        choices=RequirementDocumentMatchStatus.choices,
    )

    is_active = models.BooleanField(
        default=False,
    )

    match_reason = models.TextField(
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requirement"],
                condition=models.Q(is_active=True),
                name="unique_active_match_per_requirement",
            ),
        ]