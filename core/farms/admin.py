from django.contrib import admin

from .models import (
    Site,
    Coordinator,
    HydroponicSystem,
    Controller,
    ControllerToken,
    ControllerMessage,
    MqttMessage,
)

# Register your models here.


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    pass


@admin.register(Coordinator)
class CoordinatorAdmin(admin.ModelAdmin):
    pass


@admin.register(HydroponicSystem)
class HydroponicSystemAdmin(admin.ModelAdmin):
    pass


@admin.register(Controller)
class ControllerAdmin(admin.ModelAdmin):
    pass

@admin.register(ControllerToken)
class ControllerTokenAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ControllerTokenAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['key'].initial = ControllerToken.generate_key()
        return form

@admin.register(ControllerMessage)
class ControllerMessageAdmin(admin.ModelAdmin):
    pass


@admin.register(MqttMessage)
class MqttMessageAdmin(admin.ModelAdmin):
    pass
