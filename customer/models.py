# customer/models.py (New Address Model)
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

# Optional: Install 'django-phonenumber-field' for robust phone number handling
# pip install django-phonenumber-field
from phonenumber_field.modelfields import PhoneNumberField

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=100, blank=True, null=True)  # Optional for SSO/multi-domain later
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    subscription_type = models.CharField(
        max_length=50,
        choices=[
            ('free', 'Free'),
            ('standard', 'Standard'),
            ('premium', 'Premium')
        ],
        default='free'
    )

    def __str__(self):
        return self.name

class Address(models.Model):
    """
    A reusable address model that can be linked to a Customer for billing or delivery.
    """
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(
        max_length=10,
        choices=[('billing', 'Billing'), ('delivery', 'Delivery')],
        default='delivery'
    )
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default_billing = models.BooleanField(default=False)
    is_default_delivery = models.BooleanField(default=False)
    # You might add a field like 'label' for user-friendly names (e.g., "Home", "Work")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Addresses"
        # Ensure only one default billing/delivery address per customer
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'is_default_billing'],
                condition=models.Q(is_default_billing=True),
                name='unique_default_billing_address'
            ),
            models.UniqueConstraint(
                fields=['customer', 'is_default_delivery'],
                condition=models.Q(is_default_delivery=True),
                name='unique_default_delivery_address'
            ),
        ]

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.country} ({self.address_type})"

    def save(self, *args, **kwargs):
        # Logic to ensure only one default billing/delivery address
        if self.is_default_billing:
            Address.objects.filter(customer=self.customer, address_type='billing', is_default_billing=True).exclude(pk=self.pk).update(is_default_billing=False)
        if self.is_default_delivery:
            Address.objects.filter(customer=self.customer, address_type='delivery', is_default_delivery=True).exclude(pk=self.pk).update(is_default_delivery=False)
        super().save(*args, **kwargs)

class Customer(AbstractUser):
    company = models.ForeignKey(
        'Company', on_delete=models.CASCADE, related_name='users', null=True, blank=True
    )
    user_type = models.CharField(
        max_length=20,
        choices=[('freebie', 'Freebie'), ('company', 'Company User')],
        default='freebie'
    )
    phone_number = PhoneNumberField(blank=True, null=True, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    loyalty_points = models.IntegerField(default=0)

    PREFERRED_CONTACT_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
    ]
    preferred_contact_method = models.CharField(
        max_length=50,
        choices=PREFERRED_CONTACT_CHOICES,
        default='email',
    )
    profile_picture = models.ImageField(upload_to='customer_profiles/', null=True, blank=True)

    SIGNUP_SOURCE_CHOICES = [
        ('website', 'Website'),
        ('mobile_app', 'Mobile App'),
        ('referral', 'Referral'),
        ('social_media', 'Social Media'),
        ('admin_created', 'Admin Created'),
    ]
    signup_source = models.CharField(
        max_length=50,
        choices=SIGNUP_SOURCE_CHOICES,
        null=True,
        blank=True,
    )

    preferences = models.JSONField(default=dict, blank=True)
    phone_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"Customer: {self.username} ({self.email})"

    def update_loyalty_points(self, points):
        self.loyalty_points += points
        self.save(update_fields=['loyalty_points', 'updated_at'])

    def deactivate_account(self):
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def activate_account(self):
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])

    def verify_phone(self):
        self.phone_verified = True
        self.save(update_fields=['phone_verified', 'updated_at'])

    def update_preferences(self, new_preferences):
        if not isinstance(self.preferences, dict):
            self.preferences = {}
        self.preferences.update(new_preferences)
        self.save(update_fields=['preferences', 'updated_at'])
        
class Interaction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    INTERACTION_TYPE_CHOICES = [
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('chat', 'Chat'),
        ('support_ticket', 'Support Ticket'),
        ('note', 'Note'),
        ('website_visit', 'Website Visit'), # Example of an automated interaction
        ('quote', 'Quote Generation'), # To link to your core business
        ('order', 'Order Placed'), # To link to future order system
    ]
    interaction_type = models.CharField(
        max_length=50,
        choices=INTERACTION_TYPE_CHOICES
    )
    subject = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    interaction_date = models.DateTimeField(default=timezone.now)
    # Who initiated/handled the interaction?
    # Could be a ForeignKey to User or a new 'Employee'/'Agent' model
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_interactions')

    # Link to other models if applicable (e.g., ticket, order)
    # ticket = models.ForeignKey('SupportTicket', on_delete=models.SET_NULL, null=True, blank=True)
    # order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.interaction_type} on {self.interaction_date.strftime('%Y-%m-%d')}"
    
class Lead(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    source = models.CharField(max_length=100, choices=Customer.SIGNUP_SOURCE_CHOICES) # Re-use choices
    status = models.CharField(
        max_length=50,
        choices=[
            ('new', 'New'), ('qualified', 'Qualified'), ('contacted', 'Contacted'),
            ('unqualified', 'Unqualified'), ('converted', 'Converted')
        ],
        default='new'
    )
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# sales/models.py
class Opportunity(models.Model):
    lead = models.OneToOneField(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunity')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    # An opportunity can start from a lead and then link to a customer upon conversion

    name = models.CharField(max_length=255)
    stage = models.CharField(
        max_length=50,
        choices=[
            ('prospecting', 'Prospecting'), ('qualification', 'Qualification'),
            ('proposal', 'Proposal'), ('negotiation', 'Negotiation'),
            ('closed_won', 'Closed Won'), ('closed_lost', 'Closed Lost')
        ],
        default='prospecting'
    )
    expected_close_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    probability = models.DecimalField(max_digits=5, decimal_places=2, help_text="Probability of closing (0.00 to 1.00)", default=0.0)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_opportunities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name    

# support/models.py (or a new 'support' app)
class SupportTicket(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=[
            ('open', 'Open'), ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'), ('closed', 'Closed')
        ],
        default='open'
    )
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject}"