from greenhouse.models.water_cycle import WaterCycle
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from greenhouse.models import (
    HydroponicSystemComponent,
    WaterCycleComponent,
    WaterReservoir,
    WaterPump,
    WaterPipe,
    WaterSensor,
    WaterValve,
    PlantComponent,
    PlantSpecies,
    PlantFamily,
    PlantGenus,
    TrackingImage,
)
from iot.admin import SiteEntityAdmin


class HydroponicSystemPeripheralInline(admin.TabularInline):
    model = HydroponicSystemComponent.peripheral_component_set.through


@admin.register(HydroponicSystemComponent)
class HydroponicSystemComponentAdmin(admin.ModelAdmin):
    list_select_related = ("site_entity",)
    inlines = [HydroponicSystemPeripheralInline]


@admin.register(WaterCycle)
class WaterCycleAdmin(admin.ModelAdmin):
    pass


class WaterReservoirInline(admin.TabularInline):
    model = WaterReservoir


class WaterPumpInline(admin.TabularInline):
    model = WaterPump


class WaterPipeInline(admin.TabularInline):
    model = WaterPipe


class WaterSensorInline(admin.TabularInline):
    model = WaterSensor


class WaterValveInline(admin.TabularInline):
    model = WaterValve


class WaterCycleFlowToInline(admin.TabularInline):
    model = WaterCycleComponent.flows_to_set.through
    fk_name = 'flows_from'


class WaterCycleComponentLogInline(admin.TabularInline):
    model = WaterCycleComponent.water_cycle_log_set.through

@admin.register(WaterCycleComponent)
class WaterCycleComponentAdmin(admin.ModelAdmin):
    list_select_related = ("site_entity",)

    inlines = [
        WaterCycleComponentLogInline,
        WaterCycleFlowToInline,
        WaterReservoirInline,
        WaterPumpInline,
        WaterPipeInline,
        WaterSensorInline,
        WaterValveInline,
    ]


@admin.register(PlantComponent)
class PlantComponentAdmin(admin.ModelAdmin):
    list_select_related = ("site_entity",)


@admin.register(PlantFamily)
class PlantFaminlyAdmin(admin.ModelAdmin):
    pass


@admin.register(PlantGenus)
class PlantGenusAdmin(admin.ModelAdmin):
    pass


@admin.register(PlantSpecies)
class PlantSpeciesAdmin(admin.ModelAdmin):
    pass


@admin.register(TrackingImage)
class TrackingImageAdmin(admin.ModelAdmin):
    pass


# Inject HydroponicSystemComponent aspect into admin for SiteEntity
@mark_safe
def has_hydroponic_system(self, obj):
    try:
        return '<a href="%s">%s</a>' % (
            reverse(
                "admin:greenhouse_hydroponicsystemcomponent_change",
                args=(obj.hydroponic_system_component.pk,),
            ),
            obj.hydroponic_system_component.hydroponic_system_type,
        )
    except ObjectDoesNotExist:
        return "-"


setattr(SiteEntityAdmin, "has_hydroponic_system", has_hydroponic_system)
setattr(SiteEntityAdmin.has_hydroponic_system, "allow_tags", True)
setattr(SiteEntityAdmin.has_hydroponic_system, "short_description", "Hydroponic System")
SiteEntityAdmin.list_display.append("has_hydroponic_system")
SiteEntityAdmin.list_filter.append(
    ("hydroponic_system_component", admin.EmptyFieldListFilter)
)
SiteEntityAdmin.list_select_related.append("hydroponic_system_component")

# Inject WaterCycleComponent aspect into admin for SiteEntity
@mark_safe
def has_water_cycle(self, obj):
    try:
        types = ", ".join(obj.water_cycle_component.get_type_values())
        if not types:
            types = "yes"
        return '<a href="%s">%s</a>' % (
            reverse(
                "admin:greenhouse_watercyclecomponent_change",
                args=(obj.water_cycle_component.pk,),
            ),
            types,
        )
    except ObjectDoesNotExist:
        return "-"


setattr(SiteEntityAdmin, "has_water_cycle", has_water_cycle)
setattr(SiteEntityAdmin.has_water_cycle, "allow_tags", True)
setattr(SiteEntityAdmin.has_water_cycle, "short_description", "Water Cycle")
SiteEntityAdmin.list_display.append("has_water_cycle")
SiteEntityAdmin.list_filter.append(
    ("water_cycle_component", admin.EmptyFieldListFilter)
)
SiteEntityAdmin.list_select_related.append("water_cycle_component")
SiteEntityAdmin.list_select_related.append("water_cycle_component__water_cycle")
SiteEntityAdmin.list_select_related.append("water_cycle_component__water_reservoir")
SiteEntityAdmin.list_select_related.append("water_cycle_component__water_pipe")
SiteEntityAdmin.list_select_related.append("water_cycle_component__water_pump")
SiteEntityAdmin.list_select_related.append("water_cycle_component__water_sensor")
SiteEntityAdmin.list_select_related.append("water_cycle_component__water_valve")


# Inject PlantComponent aspect into admin for SiteEntity
@mark_safe
def has_plant(self, obj):
    try:
        return '<a href="%s">%s</a>' % (
            reverse(
                "admin:greenhouse_plantcomponent_change",
                args=(obj.plant_component.pk,),
            ),
            obj.plant_component.plant_type,
        )
    except ObjectDoesNotExist:
        return "-"


setattr(SiteEntityAdmin, "has_plant", has_plant)
setattr(SiteEntityAdmin.has_plant, "allow_tags", True)
setattr(SiteEntityAdmin.has_plant, "short_description", "Plant")
SiteEntityAdmin.list_display.append("has_plant")
SiteEntityAdmin.list_filter.append(("plant_component", admin.EmptyFieldListFilter))
SiteEntityAdmin.list_select_related.append("plant_component")
