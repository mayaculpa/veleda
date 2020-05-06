from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Coordinator

@receiver(post_delete, sender=Coordinator)
def delete_login_account(sender, instance, using, **kwargs):
    """Delete the coordinator's login account if it has one"""

    if instance.user:
        instance.user.delete()
