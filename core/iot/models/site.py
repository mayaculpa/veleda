import uuid

from address.models import AddressField
from django.db import models

from accounts.models import User

# Create your models here.
class Site(models.Model):
    """A site where plants are grown hydroponically. Contains all hydroponic systems
       and plants that are controlled by an on-site coordinator"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,)
    name = models.CharField(max_length=30, help_text="The name of the site.")
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The user that owns the site.",
    )
    address = AddressField(
        on_delete=models.SET_NULL,
        null=True,
        help_text="The postal address and the coordinates of the site",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return self.name


class SiteEntity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,)
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="site_entity",
        help_text="The site to which the site entity belongs.",
    )
    name = models.CharField(
        max_length=255,
        help_text="The name of the site entity which unifies all its components.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    def __str__(self):
        return self.name