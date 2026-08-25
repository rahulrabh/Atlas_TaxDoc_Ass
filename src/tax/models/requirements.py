from .base import BaseModel
from .employment import Employment
from .person import Person
from .tax_case import TaxCase

from django.db import models

class RequirementDocumentType(models.TextChoices):
    FORM_1040 = "FORM_1040", "Form 1040"
    GOVERNMENT_ID = "GOVERNMENT_ID", "Government ID"
    W2 = "W2", "W-2"
    UNKNOWN = "UNKNOWN", "Unknown"


class Requirement(BaseModel):
    tax_case = models.ForeignKey(
        TaxCase,
        on_delete=models.CASCADE,
        related_name="requirements",
    )

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="requirements",
        null=True,
        blank=True,
    )

    employment = models.ForeignKey(
        Employment,
        on_delete=models.CASCADE,
        related_name="requirements",
        null=True,
        blank=True,
    )

    document_type = models.CharField(
        max_length=30,
        choices=RequirementDocumentType.choices,
    )

    tax_year = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tax_case",
                    "person",
                    "employment",
                    "document_type",
                    "tax_year",
                ],
                condition=models.Q(employment__isnull=False),
                name="unique_employment_requirement",
            ),
            models.UniqueConstraint(
                fields=[
                    "tax_case",
                    "person",
                    "document_type",
                    "tax_year",
                ],
                condition=models.Q(
                    employment__isnull=True,
                    person__isnull=False,
                ),
                name="unique_person_requirement",
            ),
            models.UniqueConstraint(
                fields=[
                    "tax_case",
                    "document_type",
                    "tax_year",
                ],
                condition=models.Q(
                    employment__isnull=True,
                    person__isnull=True,
                ),
                name="unique_tax_case_requirement",
            ),
        ]