from django import forms
from address.forms import AddressField
from django.db.models import Q
from iot.models import Site, ControllerComponentType
from django.core.exceptions import ValidationError


class CreateSiteForm(forms.Form):
    name = Site._meta.get_field("name").formfield()
    address = AddressField(initial={"formatted": ""})


class CreateControllerForm(forms.Form):
    name = forms.CharField(max_length=255)
    site = forms.ModelChoiceField(Site.objects.none())
    controller_component_type = forms.ModelChoiceField(
        ControllerComponentType.objects.none(), required=False
    )
    new_type_name = forms.CharField(max_length=255, required=False)

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = Site.objects.filter(owner=owner)
        types = ControllerComponentType.objects.filter(
            Q(created_by=owner) | Q(created_by__isnull=True)
        )
        self.fields["controller_component_type"].queryset = types

    def clean(self):
        # Error if neither controller compentent type is specified
        cleaned_data = super().clean()
        if not (
            cleaned_data.get("controller_component_type")
            or cleaned_data.get("new_type_name")
        ):
            raise ValidationError("Please select an existing type or enter a new one")
