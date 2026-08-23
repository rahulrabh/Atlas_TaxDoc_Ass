from .base import BaseModel

from django.db import models

class Client(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name