from django import forms
from django.core.validators import RegexValidator
from address.forms import AddressField

from .models import Site, Coordinator


class CreateSiteForm(forms.Form):
    name = Site._meta.get_field("name").formfield()
    name.help_text = ""
    name.widget.attrs["placeholder"] = "Site's name"
    address = AddressField(initial={"formatted": ""})


class CoordinatorSetupSelectForm(forms.Form):
    """Select the coordinator to be registered"""

    coordinator_id = forms.UUIDField()


class CoordinatorSetupRegistrationForm(forms.Form):
    """Add the coordinator to the site"""

    site = forms.ModelChoiceField(Site.objects.none())
    subdomain_prefix = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "site-name"},),
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9]+[a-zA-Z0-9\-]*$",
                message="Subdomain prefix must be alphanumeric + hyphen",
                code="invalid_subdomain_prefix",
            ),
        ],
    )

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop("sites")
        super(CoordinatorSetupRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["site"].queryset = qs

    def clean_subdomain_prefix(self):
        """ensure that subdomain_prefix is always lower case."""
        return self.cleaned_data["subdomain_prefix"].lower()
