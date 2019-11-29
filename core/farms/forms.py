from django import forms
from address.forms import AddressField

from .models import Farm

class CreateFarmForm(forms.Form):
    name = Farm._meta.get_field('name').formfield()
    name.help_text = ''
    name.widget.attrs['placeholder'] = "Farm's name"
    address = AddressField(initial={'formatted': ""})
