from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse

from .models import (
    ControllerAuthToken,
    ControllerComponent,
    ControllerComponentType,
    ControllerMessage,
    ControllerTask,
    DataPoint,
    DataPointType,
    PeripheralComponent,
    PeripheralDataPointType,
    Site,
    SiteEntity,
)

# Register your models here.


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    pass


@admin.register(SiteEntity)
class SiteEntityAdmin(admin.ModelAdmin):
    @mark_safe
    def has_peripheral(self, obj):
        if obj.peripheral_component:
            return '<a href="%s">%s</a>' % (
                reverse(
                    "admin:iot_peripheralcomponent_change",
                    args=(obj.peripheral_component.pk,),
                ),
                obj.peripheral_component.peripheral_type,
            )
        return "-"

    has_peripheral.allow_tags = True
    has_peripheral.short_description = "Peripheral"

    @mark_safe
    def has_controller(self, obj):
        if obj.controller_component:
            return '<a href="%s">%s</a>' % (
                reverse(
                    "admin:iot_controllercomponent_change",
                    args=(obj.controller_component.pk,),
                ),
                obj.controller_component.component_type,
            )
        return "-"

    has_controller.allow_tags = True
    has_controller.short_description = "Controller"

    list_display = [
        "name",
        "site",
        "has_peripheral",
        "has_controller",
    ]

    list_display_links = (
        "name",
        "site",
    )

    list_filter = [
        "site",
        ("peripheral_component", admin.EmptyFieldListFilter),
        ("controller_component", admin.EmptyFieldListFilter),
    ]

    list_select_related = [
        "site",
        "peripheral_component",
        "controller_component",
    ]


@admin.register(ControllerComponentType)
class ControllerComponentTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(ControllerComponent)
class ControllerComponentAdmin(admin.ModelAdmin):
    list_select_related = ("site_entity",)


@admin.register(PeripheralComponent)
class PeripheralComponentAdmin(admin.ModelAdmin):
    list_select_related = ("site_entity",)


@admin.register(PeripheralDataPointType)
class PeripheralDataPointTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(ControllerTask)
class ControllerTaskAdmin(admin.ModelAdmin):
    pass


@admin.register(DataPointType)
class DataPointTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(DataPoint)
class DataPointAdmin(admin.ModelAdmin):
    pass


@admin.register(ControllerAuthToken)
class ControllerAuthTokenAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super(ControllerAuthTokenAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields["key"].initial = ControllerAuthToken.generate_key()
        return form


@admin.register(ControllerMessage)
class ControllerMessageAdmin(admin.ModelAdmin):
    pass
