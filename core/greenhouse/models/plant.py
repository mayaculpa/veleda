import uuid

from django.db import models
from greenhouse.models.hydroponic_system import HydroponicSystemComponent
from iot.models.site import SiteEntity


class PlantFamily(models.Model):
    """A plant family instance"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="The name of the plant family.")

    class Meta:
        verbose_name_plural = "Plant families"

    def __str__(self):
        return f"{self.name.capitalize()} family"


class PlantGenus(models.Model):
    """A plant genus instance"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="The name of the plant genus.")
    family = models.ForeignKey(
        PlantFamily,
        on_delete=models.SET_NULL,
        null=True,
        related_name="genus_set",
        help_text="The family to which the genus belongs to",
    )

    class Meta:
        verbose_name_plural = "Plant genera"

    def __str__(self):
        return f"{self.name.capitalize()} genus"


class PlantSpecies(models.Model):
    """A type of plant"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    genus = models.ForeignKey(
        PlantGenus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="species_set",
        help_text="The genus to which the species belongs to",
    )
    common_name = models.CharField(
        max_length=100, help_text="A plant type's commmon name"
    )
    binomial_name = models.CharField(
        max_length=100, help_text="A plant type's latin name."
    )

    class Meta:
        verbose_name_plural = "Plant species"

    def __str__(self):
        return self.common_name


class PlantComponent(models.Model):
    """The plant aspect of a site entity, such as a basil or tomato plant"""

    site_entity = models.OneToOneField(
        SiteEntity,
        primary_key=True,
        related_name="plant_component",
        on_delete=models.CASCADE,
        help_text="Which site entity the component is a part of.",
    )
    hydroponic_system = models.ForeignKey(
        HydroponicSystemComponent,
        on_delete=models.SET_NULL,
        null=True,
        related_name="plant_set",
        help_text="In which hydroponic system the plant is in.",
    )
    spot_number = models.IntegerField(
        blank=True,
        null=True,
        help_text="The spot in the hydroponic system in which the plant is placed.",
    )
    species = models.ForeignKey(
        PlantSpecies,
        on_delete=models.PROTECT,
        related_name="plant_set",
        help_text="The plants species as in taxus or genus",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )