import graphene
from graphene import relay
from graphql_relay.node.node import from_global_id
from greenhouse.models import WaterPump, WaterValve
from iot.graphql.mutations import Error


class WaterCycleComponentErrors(graphene.ObjectType):
    class Meta:
        interfaces = (Error,)


class TurnOnWaterPump(relay.ClientIDMutation):
    class Input:
        water_cycle_component = graphene.ID(required=True)

    errors = graphene.List(WaterCycleComponentErrors, required=True)

    @staticmethod
    def mutate_and_get_payload(root, info, water_cycle_component):
        water_cycle_component_id = from_global_id(water_cycle_component)[1]
        water_pump = WaterPump.objects.get(pk=water_cycle_component_id)
        water_pump.turn_on()
        return TurnOnWaterPump(errors=[])


class TurnOffWaterPump(relay.ClientIDMutation):
    class Input:
        water_cycle_component = graphene.ID(required=True)

    errors = graphene.List(Error, required=True)

    @staticmethod
    def mutate_and_get_payload(root, info, water_cycle_component):
        water_cycle_component_id = from_global_id(water_cycle_component)[1]
        water_pump = WaterPump.objects.get(pk=water_cycle_component_id)
        water_pump.turn_off()
        return TurnOffWaterPump(errors=[])


class SetWaterPumpPower(relay.ClientIDMutation):
    class Input:
        water_cycle_component = graphene.ID(required=True)
        power = graphene.Float(required=True)

    errors = graphene.List(Error, required=True)

    @staticmethod
    def mutate_and_get_payload(root, info, water_cycle_component, power):
        water_cycle_component_id = from_global_id(water_cycle_component)[1]
        water_pump = WaterPump.objects.get(pk=water_cycle_component_id)
        water_pump.set_power(power)
        return SetWaterPumpPower(errors=[])


class OpenWaterValve(relay.ClientIDMutation):
    class Input:
        water_cycle_component = graphene.ID(required=True)

    errors = graphene.List(Error, required=True)

    @staticmethod
    def mutate_and_get_payload(root, info, water_cycle_component):
        water_cycle_component_id = from_global_id(water_cycle_component)[1]
        water_pump = WaterValve.objects.get(pk=water_cycle_component_id)
        water_pump.open_valve()
        return OpenWaterValve(errors=[])


class CloseWaterValve(relay.ClientIDMutation):
    class Input:
        water_cycle_component = graphene.ID(required=True)

    errors = graphene.List(Error, required=True)

    @staticmethod
    def mutate_and_get_payload(root, info, water_cycle_component):
        water_cycle_component_id = from_global_id(water_cycle_component)[1]
        water_pump = WaterValve.objects.get(pk=water_cycle_component_id)
        water_pump.close_valve()
        return OpenWaterValve(errors=[])
