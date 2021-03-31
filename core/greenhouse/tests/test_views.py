import uuid
import json
import os

import urllib3
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from django.urls.base import reverse
from greenhouse.models import PlantComponent
from greenhouse.models.hydroponic_system import HydroponicSystemComponent
from greenhouse.models.plant import PlantFamily, PlantGenus, PlantSpecies
from greenhouse.models.plant_image import PlantImage
from iot.models import Site, SiteEntity
from PIL import Image


class TestPlantImage(TestCase):
    """Test views connected to plant image uploads."""

    def setUp(self):
        self.client = Client()
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self.owner_z = get_user_model().objects.create_user(
            email="ownerZ@bar.com", password="foo"
        )
        self.site_a = Site.objects.create(name="Site A", owner=self.owner_a)
        self.site_z = Site.objects.create(name="Site Z", owner=self.owner_z)
        self.family = PlantFamily.objects.create(name="Lamiaceae")
        self.genus = PlantGenus.objects.create(name="Ocimum", family=self.family)
        self.basil = PlantSpecies.objects.create(
            common_name="Basil", binomial_name="Ocimum basilicum", genus=self.genus
        )
        self.nft_system = HydroponicSystemComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="NFT1", site=self.site_a),
            hydroponic_system_type=HydroponicSystemComponent.HydroponicSystemType.NFT,
        )
        self.plant_a = PlantComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="PlntA", site=self.site_a),
            species=self.basil,
            hydroponic_system=self.nft_system,
        )
        self.image = Image.new("RGB", (800, 1280), (100, 255, 100))
        self.image.save("image.png", "PNG")
    
    def tearDown(self):
        os.remove("image.png")

    def test_create(self):
        """Test creating plant images"""

        # Check login required
        url = reverse("greenhouse:create-plant-image")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        # Test uploading an image with an ID
        self.client.force_login(self.owner_a)
        with open("image.png", "rb") as file:
            data = {"id": uuid.uuid4(), "plant": self.plant_a.pk, "image": file}
            response = self.client.post(url, data)
        self.assertContains(response, self.plant_a.pk, status_code=201)
        self.assertContains(response, self.site_a.pk, status_code=201)
        self.assertContains(response, data["id"], status_code=201)
        http = urllib3.PoolManager()
        response_data = json.loads(response.content)
        image_response = http.request("GET", response_data["image"])
        self.assertEqual(image_response.status, 200)
        data_size = os.path.getsize("image.png")
        self.assertEqual(data_size, len(image_response.data))
        PlantImage.objects.get(pk=data["id"]).delete()

        # Test uploading an image without an ID
        with open("image.png", "rb") as file:
            data = {"plant": self.plant_a.pk, "image": file}
            response = self.client.post(url, data)
        self.assertContains(response, self.plant_a.pk, status_code=201)
        self.assertContains(response, self.site_a.pk, status_code=201)
        self.assertContains(response, '"id":"', status_code=201)
        http = urllib3.PoolManager()
        response_data = json.loads(response.content)
        image_response = http.request("GET", response_data["image"])
        self.assertEqual(image_response.status, 200)
        data_size = os.path.getsize("image.png")
        self.assertEqual(data_size, len(image_response.data))
        PlantImage.objects.get(pk=response_data["id"]).delete()

        # Test uploading with missing data
        with open("image.png", "rb") as file:
            response = self.client.post(url, {"image": file})
        self.assertEqual(response.status_code, 400)

        response = self.client.post(url, {"plant": self.plant_a.pk})
        self.assertEqual(response.status_code, 400)