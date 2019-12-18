from django import forms
from django.core.validators import RegexValidator
from address.forms import AddressField

from .models import Farm, Coordinator


class CreateFarmForm(forms.Form):
    name = Farm._meta.get_field("name").formfield()
    name.help_text = ""
    name.widget.attrs["placeholder"] = "Farm's name"
    address = AddressField(initial={"formatted": ""})


class CoordinatorSetupSelectForm(forms.Form):
    """Select the coordinator to be registered"""

    coordinator_id = forms.UUIDField()


class CoordinatorSetupRegistrationForm(forms.Form):
    """Add the coordinator to the farm"""

    farm = forms.ModelChoiceField(Farm.objects.none())
    subdomain_prefix = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "farm-name"},),
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9]+[a-zA-Z0-9\-]*$",
                message="Subdomain prefix must be alphanumeric + hyphen",
                code="invalid_subdomain_prefix",
            ),
        ],
    )

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop("farms")
        super(CoordinatorSetupRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["farm"].queryset = qs

    def clean_subdomain_prefix(self):
        """ensure that subdomain_prefix is always lower case."""
        return self.cleaned_data["subdomain_prefix"].lower()
