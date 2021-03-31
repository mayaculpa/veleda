from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import UUIDField, ImageField
from greenhouse.models import PlantImage


class PlantImageSerializer(ModelSerializer):
    id = UUIDField(required=False)
    image = ImageField()

    class Meta:
        model = PlantImage
        fields = ("id", "image", "plant")

    def create(self, validated_data: dict):
        if validated_data["plant"].site_entity.site.owner != self.context["user"]:
            raise PermissionDenied(
                detail=f"{self.context['user']} not owner of plant's site"
            )
        plant_image = PlantImage.objects.create_image(
            plant_id=validated_data["plant"].pk,
            site_id=validated_data["plant"].site_entity.site_id,
            image=validated_data["image"],
            image_id=validated_data.get("id"),
        )
        return plant_image
