from django.contrib import admin

from .models import Farm, Coordinator, HydroponicSystem, Controller
# Register your models here.

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
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
