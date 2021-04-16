import json
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from graphene_django.utils.testing import GraphQLTestCase
from graphql_relay import from_global_id
from PIL import Image

from greenhouse.models import (
    HydroponicSystemComponent,
    PlantComponent,
    PlantFamily,
    PlantGenus,
    PlantImage,
    PlantSpecies,
    TrackingImage,
    WaterCycle,
    WaterCycleComponent,
    WaterCycleFlowsTo,
    WaterCycleLog,
    WaterSensor,
)
from iot.models import (
    ControllerComponent,
    ControllerComponentType,
    PeripheralComponent,
    Site,
    SiteEntity,
)


class QueryTestCase(GraphQLTestCase):
    """Test GraphQL queries"""

    def setUp(self):
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self.owner_z = get_user_model().objects.create_user(
            email="ownerB@bar.com", password="foo"
        )
        self._client.force_login(self.owner_a)

        self.site_a = Site.objects.create(name="Site A", owner=self.owner_a)
        self.site_z = Site.objects.create(name="Site Z", owner=self.owner_z)
        self.water_cycle_a = WaterCycle.objects.create(name="WC A", site=self.site_a)
        self.water_cycle_b = WaterCycle.objects.create(name="WC B", site=self.site_a)
        self.water_cycle_z = WaterCycle.objects.create(name="WC Z", site=self.site_z)
        self.family = PlantFamily.objects.create(name="Lamiaceae")
        self.genus = PlantGenus.objects.create(name="Ocimum", family=self.family)
        self.basil = PlantSpecies.objects.create(
            common_name="Basil", binomial_name="Ocimum basilicum", genus=self.genus
        )
        self.nft_system_a = HydroponicSystemComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="NFT_A", site=self.site_a),
            hydroponic_system_type=HydroponicSystemComponent.HydroponicSystemType.NFT,
        )
        self.nft_system_a_water_cycle = WaterCycleComponent.objects.create(
            site_entity=self.nft_system_a.site_entity, water_cycle=self.water_cycle_a
        )
        self.nft_system_z = HydroponicSystemComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="NFT_Z", site=self.site_z),
            hydroponic_system_type=HydroponicSystemComponent.HydroponicSystemType.NFT,
        )
        self.nft_system_z_water_cycle = WaterCycleComponent.objects.create(
            site_entity=self.nft_system_z.site_entity, water_cycle=self.water_cycle_z
        )
        self.plant_a = PlantComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="PlantA", site=self.site_a),
            species=self.basil,
            hydroponic_system=self.nft_system_a,
        )
        self.plant_z = PlantComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="PlantZ", site=self.site_z),
            species=self.basil,
            hydroponic_system=self.nft_system_z,
        )
        esp32 = ControllerComponentType.objects.create(name="ESP32")
        self.controller_component_a = ControllerComponent.objects.create(
            site_entity=SiteEntity.objects.create(site=self.site_a, name=""),
            component_type=esp32,
        )
        self.controller_component_z = ControllerComponent.objects.create(
            site_entity=SiteEntity.objects.create(site=self.site_z, name=""),
            component_type=esp32,
        )
        self.sensor_a = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(site=self.site_a, name=""),
            controller_component=self.controller_component_a,
            peripheral_type=PeripheralComponent.PeripheralType.PWM,
            state=PeripheralComponent.State.ADDED,
        )
        self.nft_system_a.peripheral_component_set.add(self.sensor_a)
        self.water_cycle_sensor_a = WaterCycleComponent.objects.create(
            site_entity=self.sensor_a.site_entity,
        )
        self.water_sensor_a = WaterSensor.objects.create(
            water_cycle_component=self.water_cycle_sensor_a,
            sensor_type=WaterSensor.SensorType.EC_METER,
        )
        now = datetime.now(tz=timezone.utc)
        WaterCycleLog.objects.create(
            water_cycle_component=self.water_cycle_sensor_a,
            water_cycle=self.water_cycle_a,
            since=now - timedelta(hours=2),
            until=now,
        )
        WaterCycleLog.objects.create(
            water_cycle_component=self.water_cycle_sensor_a,
            water_cycle=self.water_cycle_a,
            since=now,
        )
        self.sensor_z = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(site=self.site_z, name=""),
            controller_component=self.controller_component_z,
            peripheral_type=PeripheralComponent.PeripheralType.PWM,
            state=PeripheralComponent.State.ADDED,
        )
        self.nft_system_z.peripheral_component_set.add(self.sensor_z)
        self.water_cycle_sensor_z = WaterCycleComponent.objects.create(
            site_entity=self.sensor_z.site_entity,
        )
        WaterCycleLog.objects.create(
            water_cycle_component=self.water_cycle_sensor_z,
            water_cycle=self.water_cycle_z,
            since=now - timedelta(hours=2),
            until=now,
        )
        WaterCycleLog.objects.create(
            water_cycle_component=self.water_cycle_sensor_z,
            water_cycle=self.water_cycle_z,
            since=now,
        )
        self.actuator_a = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(site=self.site_a, name=""),
            controller_component=self.controller_component_a,
            peripheral_type=PeripheralComponent.PeripheralType.PWM,
            state=PeripheralComponent.State.ADDED,
        )
        self.water_cycle_actuator_a = WaterCycleComponent.objects.create(
            site_entity=self.actuator_a.site_entity, water_cycle=self.water_cycle_a
        )
        self.actuator_z = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(site=self.site_z, name=""),
            controller_component=self.controller_component_z,
            peripheral_type=PeripheralComponent.PeripheralType.PWM,
            state=PeripheralComponent.State.ADDED,
        )
        self.water_cycle_actuator_z = WaterCycleComponent.objects.create(
            site_entity=self.actuator_z.site_entity, water_cycle=self.water_cycle_z
        )
        WaterCycleFlowsTo.objects.create(
            flows_from=self.nft_system_a_water_cycle,
            flows_to=self.water_cycle_actuator_a,
        )
        WaterCycleFlowsTo.objects.create(
            flows_from=self.water_cycle_actuator_a,
            flows_to=self.water_cycle_sensor_a,
        )
        WaterCycleFlowsTo.objects.create(
            flows_from=self.water_cycle_sensor_a,
            flows_to=self.nft_system_a_water_cycle,
        )
        WaterCycleFlowsTo.objects.create(
            flows_from=self.nft_system_z_water_cycle,
            flows_to=self.water_cycle_actuator_z,
        )
        WaterCycleFlowsTo.objects.create(
            flows_from=self.water_cycle_actuator_z,
            flows_to=self.water_cycle_sensor_z,
        )
        WaterCycleFlowsTo.objects.create(
            flows_from=self.water_cycle_sensor_z,
            flows_to=self.nft_system_z_water_cycle,
        )

    def test_hydroponic_system_components(self):
        """Test that hydroponic system components are returned correctly"""

        response = self.query(
            """
            { allHydroponicSystemComponents {
                edges { node {
                    id
                    siteEntity { name }
                    hydroponicSystemType
                    peripheralComponentSet { edges { node { id } } }
                } }
            } }
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["allHydroponicSystemComponents"][
            "edges"
        ]
        output = [i["node"] for i in content]
        search_result = [
            from_global_id(i["id"])[1] == str(self.nft_system_a.pk) for i in output
        ]
        self.assertTrue(any(search_result))
        search_result = [
            from_global_id(i["id"])[1] == str(self.nft_system_z.pk) for i in output
        ]
        self.assertFalse(any(search_result))
        self.assertIn(
            output[0]["hydroponicSystemType"],
            HydroponicSystemComponent.HydroponicSystemType.values,
        )
        sensor_gid = output[0]["peripheralComponentSet"]["edges"][0]["node"]["id"]
        self.assertEqual(str(self.sensor_a.pk), from_global_id(sensor_gid)[1])

    def test_plant_components(self):
        """Test that plant components are returned correctly"""

        PlantImage.objects.create(plant=self.plant_a)
        PlantImage.objects.create(plant=self.plant_a)
        PlantImage.objects.create(plant=self.plant_z)
        response = self.query(
            """
            { allPlantComponents {
                edges { node {
                    id
                    siteEntity { name }
                    hydroponicSystem { id }
                    plantImageSet { edges { node { id } } }
                    spotNumber
                } }
            } }
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["allPlantComponents"]["edges"]
        output = [i["node"] for i in content]
        self.assertTrue(
            any(from_global_id(i["id"])[1] == str(self.plant_a.pk) for i in output)
        )
        self.assertFalse(
            any(from_global_id(i["id"])[1] == str(self.plant_z.pk) for i in output)
        )
        plant = output[0]
        self.assertEqual(plant["siteEntity"]["name"], self.plant_a.site_entity.name)
        hs_id = from_global_id(plant["hydroponicSystem"]["id"])[1]
        self.assertEqual(hs_id, str(self.nft_system_a.pk))
        self.assertEqual(len(plant["plantImageSet"]["edges"]), 2)

    def test_plant_family(self):
        """Test if plant families are returned."""

        response = self.query(
            """
            { allPlantFamilies {
                edges { node {
                    name
                    genusSet { edges { node { name } } }
                } }
            } }
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["allPlantFamilies"]["edges"]
        families = [i["node"] for i in content]
        self.assertEqual(families[0]["name"], self.family.name)
        genera = [i["node"] for i in families[0]["genusSet"]["edges"]]
        self.assertEqual(genera[0]["name"], self.genus.name)

    def test_plant_genus(self):
        """Test if plant families are returned."""

        response = self.query(
            """
            { allPlantGenera {
                edges { node {
                    name
                    family { name }
                    speciesSet { edges { node { commonName } } }
                } }
            } }
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["allPlantGenera"]["edges"]
        genera = [i["node"] for i in content]
        self.assertEqual(genera[0]["name"], self.genus.name)
        self.assertEqual(genera[0]["family"]["name"], self.family.name)
        species = [i["node"] for i in genera[0]["speciesSet"]["edges"]]
        self.assertEqual(species[0]["commonName"], self.basil.common_name)

    def test_plant_species(self):
        """Test if plant species are returned."""

        response = self.query(
            """
            { allPlantSpecies {
                edges { node {
                    commonName
                    binomialName
                    genus { name }
                    plantSet { edges { node { id } } }
                } }
            } }
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["allPlantSpecies"]["edges"]
        species = [i["node"] for i in content]
        self.assertEqual(species[0]["commonName"], self.basil.common_name)
        self.assertEqual(species[0]["binomialName"], self.basil.binomial_name)
        self.assertEqual(species[0]["genus"]["name"], self.genus.name)
        plants = [i["node"] for i in species[0]["plantSet"]["edges"]]
        self.assertEqual(from_global_id(plants[0]["id"])[1], str(self.plant_a.pk))
        self.assertEqual(len(plants), 1)

    def test_plant_image(self):
        """Test if plant images are returned correctly."""

        query = """
            { allPlantImages {
                edges { node {
                    image
                    id
                    plant { id }
                } }
            } }
            """

        plant_image_a = PlantImage.objects.create(plant=self.plant_a)
        response = self.query(query)
        self.assertResponseNoErrors(response)
        output = json.loads(response.content)["data"]["allPlantImages"]["edges"]
        plant_images = [i["node"] for i in output]
        self.assertEqual(
            from_global_id(plant_images[0]["id"])[1], str(plant_image_a.pk)
        )
        self.assertFalse(plant_images[0]["image"])
        self.assertEqual(
            from_global_id(plant_images[0]["plant"]["id"])[1], str(self.plant_a.pk)
        )
        self.assertEqual(len(plant_images), 1)

        image = Image.new("RGB", (800, 1280), (100, 255, 100))
        buffer = BytesIO()
        image.save(buffer, format="png")
        buffer.name = "image.png"
        plant_image_b = PlantImage.objects.create_image(
            plant_id=self.plant_a.pk,
            site_id=self.site_a.pk,
            image=buffer,
            image_id=uuid.uuid4(),
        )

        response = self.query(query)
        self.assertResponseNoErrors(response)
        output = json.loads(response.content)["data"]["allPlantImages"]["edges"]
        # Filter out items without an image, i.e., only keep the new item
        plant_images_b = [i["node"] for i in output if i["node"]["image"]]
        self.assertEqual(len(plant_images_b), 1)
        self.assertEqual(
            from_global_id(plant_images_b[0]["id"])[1], str(plant_image_b.pk)
        )
        self.assertIn(settings.AWS_S3_CUSTOM_DOMAIN, plant_images_b[0]["image"])

    def test_tracking_image(self):
        """Test if tracking images are queried correctly."""

        tracking_image_a = TrackingImage.objects.create(
            image_id="ID_A", hydroponic_system=self.nft_system_a, site=self.site_a
        )
        TrackingImage.objects.create(image_id="ID_Z", site=self.site_z)
        response = self.query(
            """
            { allTrackingImages {
                edges { node {
                    id
                    imageId
                    hydroponicSystem { id }
                } }
            } }
            """
        )
        self.assertResponseNoErrors(response)
        output = json.loads(response.content)["data"]["allTrackingImages"]["edges"]
        tracking_images = [i["node"] for i in output]
        self.assertEqual(len(tracking_images), 1)
        self.assertEqual(
            from_global_id(tracking_images[0]["id"])[1], str(tracking_image_a.pk)
        )
        self.assertEqual(tracking_images[0]["imageId"], tracking_image_a.image_id)
        nft_id = from_global_id(tracking_images[0]["hydroponicSystem"]["id"])[1]
        self.assertEqual(nft_id, str(self.nft_system_a.pk))

    def test_water_cycle(self):
        """Test querying water cycle and logs."""

        response = self.query(
            """
            { allWaterCycles {
                edges { node {
                    id
                    name
                    site { id }
                    waterCycleComponentLogEdges { waterCycleComponent { id } }
                    waterCycleComponentLogSet { edges { node { id } } }
                    waterCycleComponentSet { edges { node { id } } }
                } }
            } }
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["allWaterCycles"]["edges"]
        self.assertEqual(len(content), 2)
        water_cycle = [
            i["node"] for i in content if i["node"]["name"] == self.water_cycle_a.name
        ][0]
        water_cycle_id = from_global_id(water_cycle["id"])[1]
        self.assertEqual(water_cycle_id, str(self.water_cycle_a.id))
        site_id = from_global_id(water_cycle["site"]["id"])[1]
        self.assertEqual(site_id, str(self.site_a.pk))
        self.assertEqual(len(water_cycle["waterCycleComponentLogEdges"]), 2)
        self.assertEqual(len(water_cycle["waterCycleComponentLogSet"]["edges"]), 2)
        self.assertEqual(len(water_cycle["waterCycleComponentSet"]["edges"]), 2)

    def test_water_cycle_flows(self):
        """Test querying water cycle logs."""

        response = self.query(
            """
            { allWaterCycleComponents {
                edges { node {
                    id
                    waterCycle { id }
                    flowsToSet { edges { node { id } } }
                    flowsFromSet { edges { node { id } } }
                    flowsToEdges { flowsTo { id } }
                    flowsFromEdges { flowsFrom { id } }
                } }
            } }
            """
        )
        content = json.loads(response.content)["data"]["allWaterCycleComponents"][
            "edges"
        ]
        self.assertEqual(len(content), 3)
        wc_component = next(
            i["node"]
            for i in content
            if from_global_id(i["node"]["id"])[1] == str(self.actuator_a.pk)
        )
        water_cycle_id = from_global_id(wc_component["waterCycle"]["id"])[1]
        self.assertEqual(water_cycle_id, str(self.water_cycle_a.pk))
        to_id = from_global_id(wc_component["flowsToSet"]["edges"][0]["node"]["id"])[1]
        self.assertEqual(to_id, str(self.water_cycle_sensor_a.pk))
        from_id = from_global_id(
            wc_component["flowsFromSet"]["edges"][0]["node"]["id"]
        )[1]
        self.assertEqual(from_id, str(self.nft_system_a_water_cycle.pk))
        to_id = from_global_id(wc_component["flowsToEdges"][0]["flowsTo"]["id"])[1]
        self.assertEqual(to_id, str(self.water_cycle_sensor_a.pk))
        from_id = from_global_id(wc_component["flowsFromEdges"][0]["flowsFrom"]["id"])[
            1
        ]
        self.assertEqual(from_id, str(self.nft_system_a_water_cycle.pk))

    def test_water_cycle_types(self):
        """Test the query for types of water cycle components."""

        response = self.query(
            """
            { allWaterCycleComponents {
                edges { node {
                    id
                    types
                    siteEntity { hydroponicSystemComponent { id } }
                    waterReservoir { maxCapacity }
                    waterPump { power }
                    waterPipe { length }
                    waterSensor { sensorType }
                    waterValve { waterCycleComponent { id } }
                } }
            } }
            """
        )
        content = json.loads(response.content)["data"]["allWaterCycleComponents"][
            "edges"
        ]
        wc_component = next(
            i["node"]
            for i in content
            if from_global_id(i["node"]["id"])[1] == str(self.sensor_a.pk)
        )
        self.assertEqual(wc_component["types"], self.water_cycle_sensor_a.get_types())
        self.assertFalse(wc_component["waterReservoir"])
        self.assertFalse(wc_component["waterPump"])
        self.assertEqual(
            wc_component["waterSensor"]["sensorType"],
            self.water_sensor_a.sensor_type.value,
        )
        self.assertFalse(wc_component["waterValve"])


class StaticQueryTestCase(GraphQLTestCase):
    """Test that do not need a populated database."""

    def setUp(self):
        self.owner_a = get_user_model().objects.create_user(
            email="ownerA@bar.com", password="foo"
        )
        self._client.force_login(self.owner_a)

    def test_hydroponic_system_component_enums(self):
        """Test the enums for hydroponic system components."""

        response = self.query(
            """
            {
              hydroponicSystemEnums {
                hydroponicSystemType {
                  value
                  label
                }
              }
            }
            """
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)["data"]["hydroponicSystemEnums"][
            "hydroponicSystemType"
        ]
        # Check that each type and label are returned correctly
        for hs_type in HydroponicSystemComponent.HydroponicSystemType:
            item = {"value": hs_type.value, "label": hs_type.label}
            self.assertIn(item, content)
