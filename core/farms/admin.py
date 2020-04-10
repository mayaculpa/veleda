from django.contrib import admin

from .models import Site, Coordinator, HydroponicSystem, Controller, MqttMessage
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

@admin.register(MqttMessage)
class MqttMessageAdmin(admin.ModelAdmin):
    pass
