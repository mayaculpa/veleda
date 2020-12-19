from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import ControllerMessage


class ControllerMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControllerMessage
        fields = "__all__"

    def validate_message(self, message):
        message_type = message.get("type")
        if not message_type in ControllerMessage.TYPES:
            raise ValidationError(detail=f"message type not recognized: {message_type}")
        return message
