# accounts.models.user.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    tenant = models.ForeignKey(
        "accounts.Tenant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
