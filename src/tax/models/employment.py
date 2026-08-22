from .base import BaseModel
from .person import Person
from django.db import models

class Employment(BaseModel):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='employments'
    )
    employer_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.employer_name} - {self.person.name}"