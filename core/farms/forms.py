from django import forms
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
    subdomain_prefix = forms.SlugField(
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "farm_name"}),
    )

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop("farms")
        super(CoordinatorSetupRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["farm"].queryset = qs
