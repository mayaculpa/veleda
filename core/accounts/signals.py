from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, Profile

@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    if not created:
        Profile.objects.get_or_create(user=instance)
