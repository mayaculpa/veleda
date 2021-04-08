import os.path
import uuid
from typing import Optional
from uuid import UUID

from django.core.files import File
from django.db import models
from greenhouse.models import PlantComponent
from greenhouse.storage_backends import PrivateMediaStorage


class PlantImageManager(models.Manager):
    """Handles creating plant images"""

    def create_image(
        self,
        plant_id: UUID,
        site_id: UUID,
        image: File,
        image_id: Optional[UUID] = None,
    ) -> "PlantImage":
        """Create and store a new plant image for the specified plant"""

        if not image_id:
            image_id = uuid.uuid4()
        plant_image = PlantImage(id=image_id, plant_id=plant_id)
        extension = os.path.splitext(image.name)[1][1:]
        file_path = self._gen_file_path(site_id, image_id, extension)
        plant_image.image.save(file_path, image)
        return plant_image

    def _gen_file_path(self, site_id, image_id, file_ending: str) -> str:
        """Generate an image path according to the site and image IDs."""

        app_label = PlantComponent._meta.app_label
        return f"{app_label}/plant_image/{site_id}/{image_id}.{file_ending}"


class PlantImage(models.Model):
    """An image (photo) of a plant"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(
        storage=PrivateMediaStorage, editable=False, help_text="The image of a plant."
    )
    plant = models.ForeignKey(
        PlantComponent,
        on_delete=models.CASCADE,
        related_name="plant_image_set",
        help_text="The primary plant in the image.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    objects = PlantImageManager()
