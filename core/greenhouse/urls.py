from django.urls import path

from greenhouse.views_api import CreatePlantImageView

app_name = "greenhouse"

api_urlpatterns = [
    path("api/plant_image/", CreatePlantImageView.as_view(), name="create-plant-image"),
]

urlpatterns = [
    *api_urlpatterns
]
