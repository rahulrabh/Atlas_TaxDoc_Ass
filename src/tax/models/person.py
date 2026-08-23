from .base import BaseModel
from .tax_case import TaxCase

from django.db import models

class Person(BaseModel):
    class Role(models.TextChoices):
        TAXPAYER = 'PRIMARY', 'Primary Taxpayer'
        SPOUSE = 'SPOUSE', 'Spouse'
        DEPENDENT = 'DEPENDENT', 'Dependent'

    tax_case = models.ForeignKey(
        TaxCase,
        on_delete=models.CASCADE,
        related_name='people'
    )
    name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=Role.choices
    )

    def __str__(self):
        return f"{self.name} ({self.role})"
