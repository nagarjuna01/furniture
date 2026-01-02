# accounts.models.tenant.py 

from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subscription_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
