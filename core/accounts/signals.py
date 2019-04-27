from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, Profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Save a user's profile when the respective user object is saved"""
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
