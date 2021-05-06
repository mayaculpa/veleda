from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from iot.graphql.subscriptions import (
    ControllerMessageSubscription,
    DataPointSubscription,
)
from iot.models import DataPoint, FirmwareImage
from iot.models.controller import ControllerMessage


@receiver(post_save, sender=DataPoint)
def notify_data_point_subscribers(sender, instance, created, raw, **kwargs):
    """Notify all data point GraphQL subscribers of new data"""

    # Abort if the data point was not saved or is in loaddata mode
    if not created or bool(raw):
        return
    DataPointSubscription.notify_subs(instance)


@receiver(post_save, sender=ControllerMessage)
def notify_controller_message_subscribers(sender, instance, created, raw, **kwargs):
    """Notify all controller_message GraphQL subscribers of new data."""

    # Abort if the controller message was not saved or is in loaddata mode
    if not created or bool(raw):
        return
    ControllerMessageSubscription.notify_subs(instance)


@receiver(post_delete, sender=FirmwareImage)
def remove_s3_firmware_file_on_delete(instance, **kwargs):
    """On instance deletion, delete associated image stored in S3."""
    instance.file.delete(save=False)
