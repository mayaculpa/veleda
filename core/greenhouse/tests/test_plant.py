from django.test import TestCase
from django.contrib.auth import get_user_model
from iot.models import Site, SiteEntity
from greenhouse.models import (
    PlantFamily,
    PlantGenus,
    PlantSpecies,
    HydroponicSystemComponent,
    PlantComponent,
)


class TestPlant(TestCase):
    def setUp(self):
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self.site_a = Site.objects.create(name="Site A", owner=self.owner_a)
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

    def test_strings(self):
        self.assertIn(self.family.name, str(self.family))
        self.assertIn(self.genus.name, str(self.genus))
        self.assertIn(self.basil.common_name, str(self.basil))
        self.assertIn(self.plant_a.site_entity.name, str(self.plant_a))

        self.plant_a.site_entity.name = ""
        self.plant_a.site_entity.save()
        self.plant_a.refresh_from_db()
        self.assertIn(self.plant_a.species.common_name, str(self.plant_a))
