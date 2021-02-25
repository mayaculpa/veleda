import uuid

from django.db import models
from greenhouse.models import HydroponicSystemComponent


class TrackingImage(models.Model):
    """Tracking image used by the AR application"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image_id = models.CharField(
        max_length=255, help_text="The ID encoded in the tracking image"
    )
    hydroponic_system = models.ForeignKey(
        HydroponicSystemComponent,
        on_delete=models.CASCADE,
        help_text="The hydroponic system to which it is attached to.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime of creation."
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return f"Tracking image: {self.image_id}"