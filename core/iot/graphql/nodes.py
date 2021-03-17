import graphene
from django.conf import settings
from django.db.models import Q
from django_filters import BooleanFilter, FilterSet
from graphene import Date, Float, List, ObjectType, String, relay
from graphene.types.datetime import DateTime
from graphene_django import DjangoObjectType
from graphql_relay.node.node import from_global_id
from iot.models import (
    ControllerComponent,
    ControllerComponentType,
    ControllerTask,
    DataPoint,
    DataPointType,
    PeripheralComponent,
    PeripheralDataPointType,
    Site,
    SiteEntity,
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
            "created_at",
            "modified_at",
        )
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(owner=info.context.user)


class SiteEntityFilter(FilterSet):
    """Filter for SiteEntityNode that includes component filters"""

    # Add a filter for each registered component type
    for component in settings.SITE_ENTITY_COMPONENTS:
        # water_cycle_component --> is_water_cycle
        attribute_name = f"is_{component.split('_component')[0]}"
        locals()[attribute_name] = BooleanFilter(
            field_name=component, lookup_expr="isnull", exclude=True
        )

    class Meta:
        model = SiteEntity
        fields = {
            "site": ["exact"],
            "site__name": ["exact", "icontains", "istartswith"],
            "name": ["exact", "icontains", "istartswith"],
            "modified_at": ["exact", "gt", "lt"],
        }


class SiteEntityNode(DjangoObjectType):
    class Meta:
        model = SiteEntity
        filterset_class = SiteEntityFilter
        fields = [
            "id",
            "site",
            "name",
            "created_at",
            "modified_at",
        ].extend(settings.SITE_ENTITY_COMPONENTS)
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(site__owner=info.context.user)


class ControllerComponentNode(DjangoObjectType):
    class Meta:
        model = ControllerComponent
        filter_fields = {
            "site_entity": ["exact"],
            "site_entity__name": ["exact", "icontains", "istartswith"],
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

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(site_entity__site__owner=info.context.user)


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

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(
            Q(created_by=info.context.user) | Q(created_by__isnull=True)
        )


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

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(
            controller_component__site_entity__site__owner=info.context.user
        )


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
            "site_entity__name": ["exact", "icontains", "istartswith"],
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

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(site_entity__site__owner=info.context.user)

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
        fields = ("data_point_type", "peripheral", "parameter_prefix")


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

    @classmethod
    def get_queryset(cls, queryset, info):
        """Limit results to those create by themselves and global ones."""
        return queryset.filter(
            Q(created_by=info.context.user) | Q(created_by__isnull=True)
        )


class DataPointNode(DjangoObjectType):
    class Meta:
        model = DataPoint
        filter_fields = {
            "time": ["exact", "lt", "gt"],
            "peripheral_component": ["exact"],
            "peripheral_component__site_entity": ["exact"],
            "data_point_type": ["exact"],
        }
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        """Limit results to the site owner."""
        return queryset.filter(
            peripheral_component__site_entity__site__owner=info.context.user
        )


class DataPointByDayNode(ObjectType):
    """Aggregates data points by day for a given peripheral and data point type."""

    day = Date()
    avg = Float()
    min = Float()
    max = Float()

    @classmethod
    def resolve(cls, parent, info, **kwargs):
        peripheral_component_id = from_global_id(kwargs["peripheral_component"])[1]
        data_point_type_id = from_global_id(kwargs["data_point_type"])[1]
        return DataPoint.objects.by_day(
            peripheral_component_id,
            data_point_type_id,
            kwargs.get("from_date"),
            kwargs.get("before_date"),
        ).filter(peripheral_component__site_entity__site__owner=info.context.user)[:100]

    @classmethod
    def as_list_field(cls) -> "graphene.List":
        return graphene.List(
            cls,
            peripheral_component=graphene.ID(required=True),
            data_point_type=graphene.ID(required=True),
            from_date=graphene.Date(),
            before_date=graphene.Date(),
        )


class DataPointByHourNode(ObjectType):
    """Aggregates data points by the hour for a given peripheral and data point type."""

    time_hour = DateTime()
    avg = Float()
    min = Float()
    max = Float()

    @classmethod
    def resolve(cls, parent, info, **kwargs):
        peripheral_component_id = from_global_id(kwargs["peripheral_component"])[1]
        data_point_type_id = from_global_id(kwargs["data_point_type"])[1]
        return DataPoint.objects.by_hour(
            peripheral_component_id,
            data_point_type_id,
            kwargs.get("from_time"),
            kwargs.get("before_time"),
        ).filter(peripheral_component__site_entity__site__owner=info.context.user)[:100]

    @classmethod
    def as_list_field(cls) -> graphene.List:
        return graphene.List(
            cls,
            peripheral_component=graphene.ID(required=True),
            data_point_type=graphene.ID(required=True),
            from_time=graphene.DateTime(),
            before_time=graphene.DateTime(),
        )
