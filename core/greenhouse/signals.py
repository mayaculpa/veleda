from django.db.models.signals import post_delete
from django.dispatch import receiver
from greenhouse.models import PlantImage


@receiver(post_delete, sender=PlantImage)
def remove_s3_image(instance, **kwargs):
    """On instance deletion, delete associated image stored in S3"""
    instance.image.delete(save=False)
