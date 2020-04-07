from rest_framework import serializers

from .models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for a user"""
    class Meta:
        model = User
        fields = ["email", "site_set"]
