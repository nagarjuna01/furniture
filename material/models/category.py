from django.db import models
#from accounts.models import Tenant

class Category(models.Model):
    # tenant = models.ForeignKey(
    #     "accounts.Tenant",
    #     on_delete=models.CASCADE,
    #     related_name="categories"
    # )
    # ↑ Future: tenant-specific material categories

    name = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CategoryTypes(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="types"
    )
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="unique_category_type_name"
            )
        ]

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CategoryModel(models.Model):
    model_category = models.ForeignKey(
        CategoryTypes,
        on_delete=models.CASCADE,
        related_name="models"
    )
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["model_category", "name"],
                name="unique_model_name_per_category_type"
            )
        ]

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
