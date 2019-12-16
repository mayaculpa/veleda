import uuid
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
        fields = [
            "url",
            "farm",
            "local_ip_address",
            "external_ip_address",
        ]


class CoordinatorPingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex', default=uuid.uuid4)
    
    class Meta:
        model = Coordinator
        fields = [
            "id",
            "local_ip_address",
            "external_ip_address",
        ]

    def create(self, validated_data):
        coordinator, created = Coordinator.objects.update_or_create(
            id=validated_data.get("id", None),
            defaults={
                "local_ip_address": validated_data["local_ip_address"],
                "external_ip_address": validated_data["external_ip_address"],
            },
        )
        return coordinator


class HydroponicSystemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = HydroponicSystem
        fields = ["url", "farm", "name", "system_type"]


class ControllerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Controller
        fields = ["__all__"]


class ControllerPingGetSerializer(serializers.Serializer):
    controller_local_ip_address = serializers.IPAddressField()


class ControllerPingPostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex', default=uuid.uuid4)
    
    class Meta:
        model = Controller
        fields = ["__all__"]

    def create(self, validated_data):
        controller, created = Controller.objects.update_or_create(
            id=validated_data.get("id", None),
            defaults=validated_data
        )
        return controller

