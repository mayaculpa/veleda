import graphene
from graphene_django.filter import DjangoFilterConnectionField
from greenhouse.graphql.nodes import (
    HydroponicSystemComponentEnumNode,
    HydroponicSystemComponentNode,
    PlantComponentNode,
    PlantFamilyNode,
    PlantGenusNode,
    PlantSpeciesNode,
    TrackingImageNode,
    WaterComponentEnumNode,
    WaterCycleComponentNode,
    WaterCycleNode,
    WaterReservoirNode,
    WaterPumpNode,
    WaterPipeNode,
    WaterSensorNode,
    WaterValveNode,
)


class Query(object):
    """Query commands for the greenhouse GraphQL schema"""

    hydroponic_system_component = graphene.relay.Node.Field(
        HydroponicSystemComponentNode
    )
    all_hydroponic_system_components = DjangoFilterConnectionField(
        HydroponicSystemComponentNode
    )
    hydroponic_system_enums = graphene.Field(HydroponicSystemComponentEnumNode)

    plant_component = graphene.relay.Node.Field(PlantComponentNode)
    all_plant_components = DjangoFilterConnectionField(PlantComponentNode)

    plant_family = graphene.relay.Node.Field(PlantFamilyNode)
    all_plant_families = DjangoFilterConnectionField(PlantFamilyNode)

    plant_genus = graphene.relay.Node.Field(PlantGenusNode)
    all_plant_genera = DjangoFilterConnectionField(PlantFamilyNode)

    plant_species = graphene.relay.Node.Field(PlantSpeciesNode)
    all_plant_species = DjangoFilterConnectionField(PlantSpeciesNode)

    tracking_image = graphene.relay.Node.Field(TrackingImageNode)
    all_tracking_images = DjangoFilterConnectionField(TrackingImageNode)

    water_cycle = graphene.relay.Node.Field(WaterCycleNode)
    all_water_cycles = DjangoFilterConnectionField(WaterCycleNode)

    water_cycle_component = graphene.relay.Node.Field(WaterCycleComponentNode)
    all_water_cycle_components = DjangoFilterConnectionField(WaterCycleComponentNode)
    water_cycle_component_enums = graphene.Field(WaterComponentEnumNode)

    water_reservoir = graphene.relay.Node.Field(WaterReservoirNode)
    water_pump = graphene.relay.Node.Field(WaterPumpNode)
    water_pipe = graphene.relay.Node.Field(WaterPipeNode)
    water_sensor = graphene.relay.Node.Field(WaterSensorNode)
    water_valve = graphene.relay.Node.Field(WaterValveNode)
