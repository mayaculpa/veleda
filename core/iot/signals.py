from django.db.models.signals import post_save
from django.dispatch import receiver
from iot.models import DataPoint
from iot.graphql.subscriptions import DataPointSubscription


@receiver(post_save, sender=DataPoint)
def notify_data_point_graphql_subscribers(sender, instance, created, raw, **kwargs):
    """Notify all GraphQL subscribers of new data"""

    # Abort if the data point was not saved or is in loaddata mode
    if not created or bool(raw):
        return
    DataPointSubscription.new_data_point(instance)
