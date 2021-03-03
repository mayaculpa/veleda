import graphene
from django_filters import BooleanFilter, FilterSet
from graphene.types.objecttype import ObjectType
from graphene_django import DjangoObjectType
from greenhouse.models import (
    HydroponicSystemComponent,
    PlantComponent,
    PlantFamily,
    PlantGenus,
    PlantSpecies,
    TrackingImage,
    WaterCycle,
    WaterCycleComponent,
    WaterCycleFlowsTo,
    WaterCycleLog,
    WaterPipe,
    WaterPump,
    WaterReservoir,
    WaterSensor,
    WaterValve,
)
from iot.graphql.nodes import TextChoice


class HydroponicSystemComponentEnumNode(ObjectType):
    hydroponic_system_type = graphene.List(TextChoice)

    @staticmethod
    def resolve_hydroponic_system_type(parent, args):
        return [
            TextChoice(value=hs_type.value, label=hs_type.label)
            for hs_type in HydroponicSystemComponent.hydroponic_system_type
        ]


class HydroponicSystemComponentNode(DjangoObjectType):
    class Meta:
        model = HydroponicSystemComponent
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__name": ["exact", "icontains", "istartswith"],
            "site_entity__site": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "site_entity",
            "hydroponic_system_type",
            "peripheral_component_set",
            "created_at",
            "modified_at",
        )
        convert_choices_to_enum = False


class PlantComponentNode(DjangoObjectType):
    class Meta:
        model = PlantComponent
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__name": ["exact", "icontains", "istartswith"],
            "site_entity__site": ["exact"],
            "hydroponic_system": ["exact"],
            "spot_number": ["exact", "lt", "lte", "gt", "gte"],
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
        interfaces = (graphene.relay.Node,)
        filter_fields = {"name": ["exact", "icontains"]}
        fields = ("name",)


class PlantGenusNode(DjangoObjectType):
    class Meta:
        model = PlantGenus
        interfaces = (graphene.relay.Node,)
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
        interfaces = (graphene.relay.Node,)
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
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "image_id": ["exact", "icontains", "istartswith"],
            "hydroponic_system": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = ("image_id", "hydroponic_system", "created_at", "modified_at")


class WaterCycleNode(DjangoObjectType):
    class Meta:
        model = WaterCycle
        interfaces = (graphene.relay.Node,)
        filter_fields = {"name": ["exact", "icontains", "istartswith"]}


class WaterCycleComponentFilter(FilterSet):
    """Filter for WaterCycleComponentNode that includes type filters"""

    is_hydroponic_system = BooleanFilter(
        "site_entity__hydroponic_system_component", lookup_expr="isnull", exclude=True
    )
    is_water_reservoir = BooleanFilter(
        "water_reservoir", lookup_expr="isnull", exclude=True
    )
    is_water_pipe = BooleanFilter("water_pipe", lookup_expr="isnull", exclude=True)
    is_water_pump = BooleanFilter("water_pump", lookup_expr="isnull", exclude=True)
    is_water_sensor = BooleanFilter("water_sensor", lookup_expr="isnull", exclude=True)
    is_water_valve = BooleanFilter("water_valve", lookup_expr="isnull", exclude=True)

    class Meta:
        model = WaterCycleComponent
        fields = {
            "site_entity": ["exact"],
            "site_entity__name": ["exact", "icontains", "istartswith"],
            "site_entity__site": ["exact"],
        }


class WaterCycleLogNode(DjangoObjectType):
    class Meta:
        model = WaterCycleLog
        filter_fields = ["water_cycle_component", "water_cycle", "since", "until"]
        fields = ("water_cycle_component", "water_cycle", "since", "until")


class WaterCycleFlowsToNode(DjangoObjectType):
    class Meta:
        model = WaterCycleFlowsTo
        filter_fields = ["flows_from", "flows_to"]
        fields = ("flows_from", "flows_to")


class WaterCycleComponentNode(DjangoObjectType):
    types = graphene.List(graphene.String)

    class Meta:
        model = WaterCycleComponent
        filterset_class = WaterCycleComponentFilter
        interfaces = (graphene.relay.Node,)
        fields = (
            "site_entity",
            "water_cycle",
            "water_cycle_log_set",
            "water_cycle_log_edges",
            "flows_to_set",
            "flows_to_edges",
            "flows_from_set",
            "flows_from_edges",
            "water_reservoir",
            "water_pump",
            "water_pipe",
            "water_sensor",
            "water_valve",
            "created_at",
            "modified_at",
        )

    @staticmethod
    def resolve_types(water_cycle_component, args):
        return water_cycle_component.get_type_values()


class WaterComponentEnumNode(ObjectType):
    sensor_type = graphene.List(TextChoice)

    @staticmethod
    def resolve_sensor_type(parent, args):
        return [
            TextChoice(value=sensor_type.value, label=sensor_type.label)
            for sensor_type in WaterSensor.sensor_type
        ]


class WaterReservoirNode(DjangoObjectType):
    class Meta:
        model = WaterReservoir
        fields = ("max_capacity", "max_water_level")


class WaterPumpNode(DjangoObjectType):
    class Meta:
        model = WaterPump
        fields = ("water_cycle_component",)


class WaterPipeNode(DjangoObjectType):
    class Meta:
        model = WaterPipe
        fields = ("length",)


class WaterSensorNode(DjangoObjectType):
    class Meta:
        model = WaterSensor
        fields = ("sensor_type",)
        convert_choices_to_enum = False


class WaterValveNode(DjangoObjectType):
    class Meta:
        model = WaterValve
        fields = ("water_cycle_component",)
