import graphene
from graphene import relay, ObjectType, List, String
from graphene_django import DjangoObjectType
from django_filters import FilterSet, BooleanFilter

from farms.models import (
    Site,
    SiteEntity,
    ControllerComponent,
    ControllerComponentType,
    ControllerTask,
    PeripheralComponent,
    PeripheralDataPointType,
    DataPointType,
    DataPoint,
)


class TextChoice(ObjectType):
    """Maps Django's enum choices."""

    value = String()
    label = String()


class SiteNode(DjangoObjectType):
    class Meta:
        model = Site
        filter_fields = {
            "name": ["exact", "icontains", "istartswith"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "id",
            "name",
            "owner",
            "address",
            "created_at",
            "modified_at",
        )
        interfaces = (relay.Node,)


class SiteEntityFilter(FilterSet):
    """Filter for SiteEntityNode that includes component filters"""

    is_controller = BooleanFilter(
        field_name="controller_component", lookup_expr="isnull", exclude=True
    )
    is_peripheral = BooleanFilter(
        field_name="peripheral_component", lookup_expr="isnull", exclude=True
    )

    class Meta:
        model = SiteEntity
        fields = {
            "site": ["exact"],
            "name": ["exact", "icontains", "istartswith"],
            "modified_at": ["exact", "gt", "lt"],
        }


class SiteEntityNode(DjangoObjectType):
    class Meta:
        model = SiteEntity
        filterset_class = SiteEntityFilter
        fields = (
            "id",
            "site",
            "name",
            "controller_component",
            "peripheral_component",
            "created_at",
            "modified_at",
        )
        interfaces = (relay.Node,)


class ControllerComponentNode(DjangoObjectType):
    class Meta:
        model = ControllerComponent
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__site": ["exact"],
            "component_type": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "site_entity",
            "component_type",
            "peripheral_component_set",
            "created_at",
            "modified_at",
        )
        interfaces = (relay.Node,)


class ControllerComponentTypeNode(DjangoObjectType):
    class Meta:
        model = ControllerComponentType
        filter_fields = {
            "id": ["exact"],
            "name": ["exact", "icontains", "istartswith"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "id",
            "name",
            "created_at",
            "modified_at",
        )
        interfaces = (relay.Node,)


class ControllerTaskNode(DjangoObjectType):
    class Meta:
        model = ControllerTask
        filter_fields = {
            "id": ["exact"],
            "controller_component": ["exact"],
            "task_type": ["exact"],
            "state": ["exact"],
            "run_until": ["exact", "lt", "gt"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "id",
            "controller_component",
            "task_type",
            "state",
            "run_until",
            "created_at",
            "modified_at",
            "parameters",
        )
        convert_choices_to_enum = False
        interfaces = (relay.Node,)


class ControllerTaskEnumNode(ObjectType):
    states = List(TextChoice)
    task_types = List(TextChoice)

    @staticmethod
    def resolve_states(parent, args):
        return [
            TextChoice(value=state.value, label=state.label)
            for state in ControllerTask.State
        ]
    
    @staticmethod
    def resolve_task_types(parent, args):
        return [
            TextChoice(value=task_type.value, label=task_type.label)
            for task_type in ControllerTask.TaskType
        ]


class PeripheralComponentNode(DjangoObjectType):
    class Meta:
        model = PeripheralComponent
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__site": ["exact"],
            "controller_component": ["exact"],
            "peripheral_type": ["exact"],
            "state": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "site_entity",
            "controller_component",
            "peripheral_type",
            "state",
            "parameters",
            "other_parameters",
            "data_point_set",
            "data_point_type_set",
            "data_point_type_edges",
            "created_at",
            "modified_at",
        )
        convert_choices_to_enum = False
        interfaces = (relay.Node,)

    parameters = graphene.JSONString(
        description="Combines other parameters and data point types to create controller commands."
    )

    @staticmethod
    def resolve_parameters(peripheral_component, _):
        """The parameter fields combines all parameters"""

        return peripheral_component.parameters


class PeripheralComponentEnumNode(ObjectType):
    states = List(TextChoice)
    peripheral_types = List(TextChoice)

    @staticmethod
    def resolve_states(parent, args):
        return [
            TextChoice(value=state.value, label=state.label)
            for state in PeripheralComponent.State
        ]

    @staticmethod
    def resolve_peripheral_types(parent, args):
        return [
            TextChoice(value=peripheral_type.value, label=peripheral_type.label)
            for peripheral_type in PeripheralComponent.PeripheralType
        ]


class PeripheralDataPointTypeNode(DjangoObjectType):
    class Meta:
        model = PeripheralDataPointType
        filter_fields = ["data_point_type", "peripheral", "parameter_prefix"]
        fields = fields = ("data_point_type", "peripheral", "parameter_prefix")


class DataPointTypeNode(DjangoObjectType):
    class Meta:
        model = DataPointType
        filter_fields = {
            "name": ["exact", "icontains", "istartswith"],
            "unit": ["exact", "icontains", "istartswith"],
            "peripheral_component_set": ["exact"],
            "peripheral_component_set__site_entity": ["exact"],
        }
        fields = (
            "name",
            "unit",
            "data_point_set",
            "peripheral_component_set",
            "peripheral_component_edges",
        )
        interfaces = (relay.Node,)


class DataPointNode(DjangoObjectType):
    class Meta:
        model = DataPoint
        filter_fields = {
            "time": ["exact", "lt", "gt"],
            "peripheral_component": ["exact"],
            "peripheral_component__site_entity": ["exact"],
            "data_point_type": ["exact"],
            "value": ["exact", "lt", "gt"],
        }
        interfaces = (relay.Node,)
