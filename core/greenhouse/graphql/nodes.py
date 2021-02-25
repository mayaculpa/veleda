from graphene import relay
from graphene_django import DjangoObjectType
from greenhouse.models import (
    HydroponicSystemComponent,
    PlantComponent,
    PlantFamily,
    PlantGenus,
    PlantSpecies,
    TrackingImage,
    WaterCycleComponent,
)


class HydroponicSystemComponentNode(DjangoObjectType):
    class Meta:
        model = HydroponicSystemComponent
        interfaces = (relay.Node,)
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__name": ["exact", "icontains", "istartswith"],
            "site_entity__site": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "site_entity",
            "peripheral_component_set",
            "created_at",
            "modified_at",
        )


class PlantComponentNode(DjangoObjectType):
    class Meta:
        model = PlantComponent
        interfaces = (relay.Node,)
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__name": ["exact", "icontains", "istartswith"],
            "site_entity__site": ["exact"],
            "species": ["exact"],
            "species__common_name": ["exact", "icontains"],
            "species__binomial_name": ["exact", "icontains"],
            "species__genus": ["exact"],
            "species__genus__name": ["exact", "icontains"],
            "species__genus__family": ["exact"],
            "species__genus__family__name": ["exact", "icontains"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "site_entity",
            "peripheral_component_set",
            "spot_number",
            "species",
            "created_at",
            "modified_at",
        )


class PlantFamilyNode(DjangoObjectType):
    class Meta:
        model = PlantFamily
        interfaces = (relay.Node,)
        filter_fields = {"name": ["exact", "icontains"]}
        fields = ("name",)


class PlantGenusNode(DjangoObjectType):
    class Meta:
        model = PlantGenus
        interfaces = (relay.Node,)
        filter_fields = {
            "name": ["exact", "icontains"],
            "family": ["exact"],
            "family__name": ["exact", "icontains"],
        }
        fields = (
            "name",
            "family",
        )


class PlantSpeciesNode(DjangoObjectType):
    class Meta:
        model = PlantSpecies
        interfaces = (relay.Node,)
        filter_fields = {
            "common_name": ["exact", "icontains"],
            "binomial_name": ["exact", "icontains"],
            "genus": ["exact"],
            "genus__name": ["exact", "icontains"],
            "genus__family": ["exact"],
            "genus__family__name": ["exact", "icontains"],
        }
        fields = (
            "common_name",
            "binomial_name",
        )


class TrackingImageNode(DjangoObjectType):
    class Meta:
        model = TrackingImage
        interfaces = (relay.Node,)
        filter_fields = {
            "image_id": ["exact", "icontains", "istartswith"],
            "hydroponic_system": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = ("image_id", "hydroponic_system", "created_at", "modified_at")


class WaterCycleComponentNode(DjangoObjectType):
    class Meta:
        model = WaterCycleComponent
        interfaces = (relay.Node,)
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__name": ["exact", "icontains", "istartswith"],
        }
        fields = (
            "site_entity",
            "peripheral_component_set",
            "reservoir_capacity",
            "reservoir_height",
            "created_at",
            "modified_at",
        )
