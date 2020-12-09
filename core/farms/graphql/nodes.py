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
    DataPointType,
    DataPoint,
)


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
            "id",
            "component_type",
            "site_entity",
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
    state_values = List(String)
    state_labels = List(String)
    task_type_values = List(String)
    task_type_labels = List(String)

    @staticmethod
    def resolve_state_values(parent, args):
        return ControllerTask.State.values

    @staticmethod
    def resolve_state_labels(parent, args):
        return ControllerTask.State.labels

    @staticmethod
    def resolve_task_type_values(parent, args):
        return ControllerTask.TaskType.values

    @staticmethod
    def resolve_task_type_labels(parent, args):
        return ControllerTask.TaskType.labels


class PeripheralComponentNode(DjangoObjectType):
    class Meta:
        model = PeripheralComponent
        filter_fields = {
            "id": ["exact"],
            "site_entity": ["exact"],
            "site_entity__site": ["exact"],
            "controller_component": ["exact"],
            "peripheral_type": ["exact"],
            "state": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "modified_at": ["exact", "lt", "gt"],
        }
        fields = (
            "id",
            "site_entity",
            "controller_component",
            "peripheral_type",
            "state",
            "parameters",
            "data_point_set",
            # "data_point_types",
            # "data_point_type_edges",
            "created_at",
            "modified_at",
        )
        convert_choices_to_enum = False
        interfaces = (relay.Node,)

    data_point_types = graphene.JSONString()

    @staticmethod
    def resolve_data_point_types(peripheral_component, _):
        """DataPointTypes is a property and therefore has to manually be set"""

        return peripheral_component.data_point_types


class DataPointTypeNode(DjangoObjectType):
    class Meta:
        model = DataPointType
        filter_fields = {
            "name": ["exact", "icontains", "istartswith"],
            "unit": ["exact", "icontains", "istartswith"],
        }
        fields = (
            "name",
            "unit",
            "data_point_set",
        )
        interfaces = (relay.Node,)


class DataPointNode(DjangoObjectType):
    class Meta:
        model = DataPoint
        filter_fields = {
            "time": ["exact", "lt", "gt"],
            "peripheral_component": ["exact"],
            "data_point_type": ["exact"],
            "value": ["exact", "lt", "gt"],
        }
        interfaces = (relay.Node,)
