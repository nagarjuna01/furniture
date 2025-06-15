from django.db import models
from django.utils import timezone
#from geopy.geocoders import Nominatim

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    
    # Billing Address Fields
    billing_street_address = models.CharField(max_length=255,null= True, blank= True)
    billing_city = models.CharField(max_length=100,null= True, blank= True)
    billing_state = models.CharField(max_length=100,null= True, blank= True)
    billing_postal_code = models.CharField(max_length=20,null= True, blank= True)
    billing_country = models.CharField(max_length=100,null= True, blank= True)
    
    # Delivery Address Fields
    delivery_street_address = models.CharField(max_length=255,null= True, blank= True)
    delivery_city = models.CharField(max_length=100,null= True, blank= True)
    delivery_state = models.CharField(max_length=100,null= True, blank= True)
    delivery_postal_code = models.CharField(max_length=20,null= True, blank= True)
    delivery_country = models.CharField(max_length=100,null= True, blank= True)
    
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional Fields
    date_of_birth = models.DateField(null=True, blank=True)
    loyalty_points = models.IntegerField(default=0)
    preferred_contact_method = models.CharField(
        max_length=50,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('sms', 'SMS')
        ],
        default='email'
    )
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='customer_profiles/', null=True, blank=True)
    signup_source = models.CharField(
        max_length=50,
        choices=[
            ('website', 'Website'),
            ('mobile_app', 'Mobile App'),
            ('referral', 'Referral'),
            ('social_media', 'Social Media')
        ],
        null=True,
        blank=True
    )
    preferences = models.JSONField(default=dict, blank=True)
    address_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def update_loyalty_points(self, points):
        self.loyalty_points += points
        self.save()

    def deactivate_account(self):
        self.is_active = False
        self.save()

    def activate_account(self):
        self.is_active = True
        self.save()

    def verify_address(self):
        self.address_verified = True
        self.save()

    def verify_phone(self):
        self.phone_verified = True
        self.save()

    def update_preferences(self, new_preferences):
        self.preferences.update(new_preferences)
        self.save()

    def last_login_update(self):
        self.last_login = timezone.now()
        self.save()

    #def get_locality_from_postal_code(self, postal_code):
        #geolocator = Nominatim(user_agent="myGeocoder")
        #location = geolocator.geocode(postal_code)
        
        #if location:
        #     address = location.address.split(", ")
        #     return {
        #         "country": address[-1],
        #         "state": address[-2],
        #         "city": address[-3],
        #         "area": address[-4] if len(address) > 3 else None
        #     }
        # return None
