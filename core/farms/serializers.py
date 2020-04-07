import uuid
from rest_framework import serializers
from address.models import Address
from accounts.models import User

from .models import Site, Coordinator, Controller, HydroponicSystem, MqttMessage


class SiteAddressSerializer(serializers.ModelSerializer):
    """Nested serializer for a site's address"""
    class Meta:
        model = Address
        fields = [
            "raw",
        ]


class SiteOwnerField(serializers.HyperlinkedRelatedField):
    """Field to only list the logged in user. In future all group members?"""
    # How to limit related members https://stackoverflow.com/a/57184103

    def get_queryset(self):
        user = self.context["request"].user
        return User.objects.filter(pk=user.id)


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """Serialize a farm site and limit owner and address listings"""
    address = SiteAddressSerializer()
    owner = SiteOwnerField(view_name="user-detail")

    class Meta:
        model = Site
        fields = ["url", "name", "owner", "address"]


class CoordinatorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Coordinator
        fields = [
            "url",
            "site",
            "local_ip_address",
            "external_ip_address",
        ]

class MqttMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MqttMessage
        fields = [
            "timestamp",
            "coordinator",
            "message",
            "controller",
            "topic_prefix",
            "topic_suffix",
        ]

class CoordinatorPingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)

    class Meta:
        model = Coordinator
        fields = [
            "id",
            "local_ip_address",
            "external_ip_address",
        ]

    def create(self, validated_data):
        coordinator, created = Coordinator.objects.update_or_create(
            id=validated_data.get("id", None), defaults=validated_data
        )
        return coordinator


class HydroponicSystemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = HydroponicSystem
        fields = ["url", "site", "name", "system_type"]


class ControllerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Controller
        fields = "__all__"


class ControllerPingGetSerializer(serializers.Serializer):
    coordinator_local_ip_address = serializers.IPAddressField(allow_blank=True)


class ControllerPingPostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)

    class Meta:
        model = Controller
        fields = [
            "id",
            "name",
            "wifi_mac_address",
            "external_ip_address",
            "controller_type",
        ]

    def create(self, validated_data):
        controller, created = Controller.objects.update_or_create(
            id=validated_data.get("id", None), defaults=validated_data
        )
        return controller
