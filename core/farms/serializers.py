import uuid

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from address.models import Address

from .models import (
    Site,
    Coordinator,
    Controller,
    ControllerMessage,
    HydroponicSystem,
    MqttMessage,
    User,
)


class SiteAddressSerializer(serializers.ModelSerializer):
    """Nested serializer for a site's address"""

    class Meta:
        model = Address
        fields = [
            "street_number",
            "route",
            "locality",
            "raw",
            "formatted",
            "latitude",
            "longitude",
        ]
        read_only_fields = [
            "street_number",
            "route",
            "locality",
            "formatted",
            "latitude",
            "longitude",
        ]


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """Serialize a farm site and limit owner and address listings"""

    address = SiteAddressSerializer()

    class Meta:
        model = Site
        fields = ["url", "name", "owner", "address", "coordinator_set"]
        read_only_fields = ["coordinator_set", "owner"]

    def create(self, validated_data):
        """Create a new site with the logged in user as owner"""
        return Site.objects.create(**validated_data, owner=self.context["request"].user)

    def update(self, instance, validated_data):
        """Only support PUT. validated data must contain name + address.raw"""
        address_raw = validated_data["address"]["raw"]
        if instance.address.raw != address_raw:
            instance.address.delete()
            instance.address = Address.objects.create(raw=address_raw)
        instance.name = validated_data["name"]
        instance.save()
        return instance


class CoordinatorSiteField(serializers.HyperlinkedRelatedField):
    """Field to only list sites owned by user"""

    def get_queryset(self):
        user = self.context["request"].user
        return Site.objects.filter(owner=user.id)


class CoordinatorMqttMessagesField(serializers.HyperlinkedRelatedField):
    """Field to list MQTT messages in a coordinator"""

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
    email = serializers.EmailField(read_only=True, source="user.email")
    password = serializers.CharField(write_only=True, max_length=100, required=False)
    mqttmessage_set = CoordinatorMqttMessagesField(read_only=True, many=True)

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        coordinator = super().create(validated_data)

        if password:
            coordinator.create_user_account(password, False)
        return coordinator

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        coordinator = super().update(instance, validated_data)

        if password:
            if coordinator.user:
                coordinator.user.set_password(password)
                coordinator.user.save()
            else:
                coordinator.create_user_account(password)
        return coordinator

    class Meta:
        model = Coordinator
        fields = [
            "url",
            "site",
            "email",
            "password",
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


class WsMqttMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MqttMessage
        fields = "__all__"


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


class ControllerMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControllerMessage
        fields = "__all__"

    def validate_message(self, message):
        message_type = message.get("type")
        if not message_type in ControllerMessage.TYPES:
            raise ValidationError(detail=f"message type not recognized: {message_type}")
        return message


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
