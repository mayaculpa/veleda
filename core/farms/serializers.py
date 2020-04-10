import uuid
from rest_framework import serializers
from rest_framework.reverse import reverse
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

    address = SiteAddressSerializer(read_only=True)
    owner = SiteOwnerField(view_name="user-detail", read_only=True)

    class Meta:
        model = Site
        fields = ["url", "name", "owner", "address", "coordinator_set"]
        read_only_fields = ["coordinator_set"]

    def create(self, validated_data):
        validated_data.pop("coordinator_set")
        return Site.objects.create(**validated_data, owner=self.context["request"].user)


class CoordinatorSiteField(serializers.HyperlinkedRelatedField):
    """Field to only list sites owned by user"""

    def get_queryset(self):
        user = self.context["request"].user
        return Site.objects.filter(owner=user.id)


class CoordinatorMqttMessagesField(serializers.HyperlinkedRelatedField):
    # We define these as class attributes, so we don't need to pass them as arguments.
    view_name = "mqttmessage-detail"

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {"pk": obj.coordinator.id, "created_at": str(obj.created_at)}
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        lookup_kwargs = {
            "coordinator": view_kwargs["pk"],
            "created_at": view_kwargs["created_at"],
        }
        return self.get_queryset().get(**lookup_kwargs)


class CoordinatorSerializer(serializers.HyperlinkedModelSerializer):
    """Serialize a coordinator and limit site selection to own sites"""

    site = CoordinatorSiteField(view_name="site-detail")
    mqttmessage_set = CoordinatorMqttMessagesField(read_only=True, many=True)

    class Meta:
        model = Coordinator
        fields = [
            "url",
            "site",
            "local_ip_address",
            "external_ip_address",
            "mqttmessage_set",
        ]


class MqttMessageSerializer(serializers.ModelSerializer):
    url = CoordinatorMqttMessagesField(read_only=True)

    class Meta:
        model = MqttMessage
        fields = [
            "url",
            "created_at",
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
