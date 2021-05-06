from typing import Optional
import os
import uuid
import hashlib

from django.db import models
from django.core.files import File
from semantic_version import Version

from iot.storage_backends import PrivateMediaStorage


class FirmwareImageManager(models.Manager):
    """Handles uploading firmware images."""

    def create_image(
        self,
        name: str,
        version: Version,
        file: File,
        file_id: Optional[uuid.UUID] = None,
    ) -> "FirmwareImage":
        """Create and store a new firmware image."""
        if not file_id:
            file_id = uuid.uuid4()
        # Check if the supplied version is a valid semantic version number
        Version(version)
        # Generate a hash from the file
        file_hash = self.generate_hash_digest(file)
        firmware_image = self.model(
            id=file_id, name=name, version=version, hash_sha3_512=file_hash
        )
        filename = self.generate_filename(file, name, version)
        firmware_image.file.save(filename, file)
        return firmware_image

    @staticmethod
    def generate_hash_digest(file) -> bytes:
        """Generate a sha3 512 hash digest for the given file."""
        file.seek(0)
        return hashlib.sha3_512(file.read()).digest()

    @staticmethod
    def generate_filename(file, name, version) -> str:
        """Generate a filename based on the firmware name and version."""
        extension = os.path.splitext(file.name)[1][1:]
        return f"{name}_{version}.{extension}"

    @staticmethod
    def generate_path(instance, filename) -> str:
        """Create file path for a given instance and file name."""
        app_label = instance._meta.app_label
        return f"{app_label}/firmware_image/{filename}"


class FirmwareImage(models.Model):
    """A specific firmware file and version."""

    class Meta:
        unique_together = ["name", "version"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        help_text="The name of the firmware excluding version number.",
    )
    version = models.CharField(
        max_length=255, help_text="The semantic version of the image."
    )
    file = models.FileField(
        storage=PrivateMediaStorage,
        upload_to=FirmwareImageManager.generate_path,
        help_text="The file of the firmware image.",
    )
    hash_sha3_512 = models.BinaryField(
        max_length=64, help_text="The sha3-512 hash of the uploaded file."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime of creation."
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    objects = FirmwareImageManager()

    def __str__(self):
        return f"{self.name} ({self.version})"
