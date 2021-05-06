from typing import Any

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from semantic_version.base import Version

from iot.models import (
    ControllerAuthToken,
    ControllerComponent,
    ControllerComponentType,
    ControllerMessage,
    ControllerTask,
    DataPoint,
    DataPointType,
    FirmwareImage,
    PeripheralComponent,
    PeripheralDataPointType,
    Site,
    SiteEntity,
)
from iot.models.controller import _generate_auth_token
from iot.models.firmware_images import FirmwareImageManager


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
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["key"].initial = _generate_auth_token()
        return form


@admin.register(ControllerMessage)
class ControllerMessageAdmin(admin.ModelAdmin):
    pass


class FirmwareImageAdminForm(forms.ModelForm):
    class Meta:
        model = FirmwareImage
        fields = ("name", "version", "file")

    def clean_file(self):
        """Only allow creating, not updating instances."""
        if self.instance and self.instance.created_at:
            raise forms.ValidationError(
                "You cannot modify the file. Please create a new instance."
            )
        return self.cleaned_data["file"]

    def clean_version(self):
        """Check if it is a valid version number."""
        version = self.cleaned_data["version"]
        try:
            Version(version)
        except ValueError as err:
            raise forms.ValidationError("Invalid semantic version number") from err
        return version

    def save(self, commit: bool = True) -> Any:
        """Overrides to check semantic version, generate the hash and filename."""
        Version(self.instance.version)
        self.instance.hash_sha3_512 = FirmwareImageManager.generate_hash_digest(
            self.instance.file
        )
        self.instance.file.name = FirmwareImageManager.generate_filename(
            self.instance.file, self.instance.name, self.instance.version
        )
        return super().save(commit=commit)


@admin.register(FirmwareImage)
class FirmwareImageAdmin(admin.ModelAdmin):
    form = FirmwareImageAdminForm
    readonly_fields = ("sha_hash",)

    def sha_hash(self, obj: FirmwareImage):
        """Convert the binary SHA3 hash to hex."""
        return obj.hash_sha3_512.hex()

    sha_hash.short_description = "Hash (SHA3-512)"
