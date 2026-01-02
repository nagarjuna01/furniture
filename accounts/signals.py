from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Tenant, GlobalVariable

@receiver(post_save, sender=Tenant)
def populate_default_global_variables(sender, instance, created, **kwargs):
    """
    Automatically creates the 'Furniture DNA' for every new tenant.
    """
    if created:
        defaults = [
            {'name': 'Side Thickness', 'abbr': '@ST', 'value': 18.0},
            {'name': 'Horizontal Thickness', 'abbr': '@HT', 'value': 18.0},
            {'name': 'Back Thickness', 'abbr': '@BT', 'value': 9.0},
            {'name': 'Door Reveal', 'abbr': '@DR', 'value': 2.0},
            {'name': 'Toe Kick Height', 'abbr': '@TK', 'value': 100.0},
            {'name': 'Back Panel Inset', 'abbr': '@BI', 'value': 20.0},
        ]
        
        # Create all defaults for this specific tenant instance
        for var in defaults:
            GlobalVariable.objects.create(
                tenant=instance,
                name=var['name'],
                abbr=var['abbr'],
                value=var['value']
            )