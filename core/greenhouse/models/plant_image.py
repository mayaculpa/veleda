import os.path
import uuid
from typing import Optional
from uuid import UUID

from django.core.files import File
from django.db import models

from greenhouse.models import PlantComponent
from iot.storage_backends import PrivateMediaStorage


class PlantImageManager(models.Manager):
    """Handles creating plant images."""

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
        filename = self.generate_filename(image, image_id)
        plant_image.image.save(filename, image)
        return plant_image

    @staticmethod
    def generate_filename(file: File, image_id: UUID) -> str:
        extension = os.path.splitext(file.name)[1][1:]
        return f"{image_id}.{extension}"

    @staticmethod
    def generate_path(instance: "PlantImage", filename: str) -> str:
        """Create file path for a given instance and file name."""
        app_label = instance._meta.app_label
        site_id = instance.plant.site_entity.site_id
        return f"{app_label}/plant_image/{site_id}/{filename}"


class PlantImage(models.Model):
    """An image (photo) of a plant"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(
        storage=PrivateMediaStorage,
        upload_to=PlantImageManager.generate_path,
        editable=False,
        help_text="The image of a plant.",
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
