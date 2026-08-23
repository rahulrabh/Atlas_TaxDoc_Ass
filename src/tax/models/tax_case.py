from .base import BaseModel
from .client import Client

from django.db import models

class TaxCase(BaseModel):
    class FilingStatus(models.TextChoices):
        SINGLE = 'SINGLE', 'Single'
        MARRIED_JOINTLY = 'MFJ', 'Married Filing Jointly'
        MARRIED_SEPARATELY = 'MFS', 'Married Filing Separately'
        HEAD_OF_HOUSEHOLD = 'HOH', 'Head of Household'

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='tax_cases'
    )
    tax_year = models.IntegerField()
    filing_status = models.CharField(
        max_length=10,
        choices=FilingStatus.choices,
        default=FilingStatus.SINGLE
    )

    def __str__(self):
        return f"{self.client.name} - {self.tax_year} ({self.filing_status})"
