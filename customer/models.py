from django.db import models
from django.utils import timezone
from accounts.models.base import TenantModel

class Client(TenantModel):
    """
    External customer/client for CRM (belongs to a tenant).
    """
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("tenant", "email")

    def __str__(self):
        return self.name

class Lead(TenantModel):
    SOURCE_CHOICES = [
        ("website", "Website"),
        ("referral", "Referral"),
        ("email_campaign", "Email Campaign"),
        ("phone", "Phone Call"),
        ("social_media", "Social Media"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("unqualified", "Unqualified"),
        ("converted", "Converted"),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="leads",
        null=True,
        blank=True
    )

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default="website")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="new")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

class Opportunity(TenantModel):
    STAGE_CHOICES = [
        ("prospecting", "Prospecting"),
        ("qualification", "Qualification"),
        ("proposal", "Proposal"),
        ("negotiation", "Negotiation"),
        ("closed_won", "Closed Won"),
        ("closed_lost", "Closed Lost"),
    ]

    lead = models.OneToOneField(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunity"
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="opportunities",
        null=True,
        blank=True
    )

    name = models.CharField(max_length=255)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default="prospecting")
    expected_close_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "stage"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.stage})"
class SupportTicket(TenantModel):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=True,
        blank=True
    )

    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="open")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status", "priority"]),
        ]

    def __str__(self):
        return f"Ticket #{self.pk}: {self.subject}"
class Interaction(TenantModel):
    INTERACTION_TYPE_CHOICES = [
        ("call", "Call"),
        ("email", "Email"),
        ("meeting", "Meeting"),
        ("chat", "Chat"),
        ("note", "Note"),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="interactions",
        null=True,
        blank=True
    )

    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPE_CHOICES)
    subject = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    interaction_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-interaction_date"]
        indexes = [
            models.Index(fields=["tenant", "interaction_type"]),
        ]

    def __str__(self):
        return f"{self.client.name if self.client else 'Unknown'} - {self.interaction_type}"
