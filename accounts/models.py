from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Phase-1 custom user model.
    No tenant field yet. Fully compatible with JWT.
    """
    pass