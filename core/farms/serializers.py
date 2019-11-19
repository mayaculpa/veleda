from rest_framework import serializers
from address.models import Address

from .models import Farm, Coordinator, Controller, HydroponicSystem


class FarmSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Farm
        fields = ["url", "name", "owner", "address"]


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = [
            "url",
            "raw",
            "country",
            "country_code",
            "state",
            "state_code",
            "locality",
            "sublocality",
            "postal_code",
            "street_number",
            "route",
            "formatted",
            "latitude",
            "longitude",
        ]


class CoordinatorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Coordinator
        fields = ["url", "farm", "local_ip", "dns_address"]


class HydroponicSystemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = HydroponicSystem
        fields = ["url", "farm", "name", "system_type"]


class ControllerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Controller
        fields = ["url", "name", "wifi_mac", "controller_type"]
