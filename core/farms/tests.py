import pytz
import uuid
from datetime import datetime, timedelta
from unittest import mock

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from address.models import Address

from .models import Farm, Coordinator, HydroponicSystem, Controller
from accounts.models import Profile


# Create your tests here.
class FarmTests(TestCase):
    def setUp(self):
        pass
        # self.client = Client()

    def test_farm_components(self):
        """Test creating a farm and its components."""

        proto_farm_owner = get_user_model().objects.create_user(
            email="owner@example.com", password="owners_passwd",
        )
        proto_farm_owner.profile.short_name = "Dude"
        proto_farm_owner.profile.full_name = "Dr. Owner C. Dude"
        proto_farm_owner.save()

        proto_farm_address = Address.objects.create(
            raw="Some Street 42, Any Town, Major City, New Country",
        )
        farm = Farm.objects.create(
            name="ProtoFarm", owner=proto_farm_owner, address=proto_farm_address
        )
        self.assertEqual(
            farm.owner.profile.short_name, proto_farm_owner.profile.short_name
        )
        self.assertEqual(farm.address.raw, proto_farm_address.raw)

        coordinator = Coordinator.objects.create(farm=farm)
        hydroponic_system_a = HydroponicSystem.objects.create(farm=farm,)
        hydroponic_system_b = HydroponicSystem.objects.create(farm=farm,)
        controller_a = Controller.objects.create(
            farm=farm,
            controller_type=Controller.SENSOR_CONTROLLER,
            wifi_mac_address="00:11:22:33:44:55",
        )
        controller_b = Controller.objects.create(
            farm=farm,
            controller_type=Controller.PUMP_CONTROLLER,
            wifi_mac_address="00:11:22:33:44:56",
        )
        self.assertEqual(farm.coordinator.id, coordinator.id)
        self.assertEqual(controller_a.farm.id, farm.id)
        self.assertEqual(controller_b.farm.id, farm.id)
        self.assertEqual(hydroponic_system_a.farm.id, farm.id)
        self.assertEqual(hydroponic_system_b.farm.id, farm.id)

    def test_farm_timestamps(self):
        """Test creating a farm and check that the timestamps update correctly"""

        mocked_now = datetime.now(pytz.utc)
        with mock.patch("django.utils.timezone.now", return_value=mocked_now):
            farm = Farm.objects.create(name="ProtoFarm")
            coordinator = Coordinator.objects.create(farm=farm)
            hydroponic_system = HydroponicSystem.objects.create(
                farm=farm, system_type=HydroponicSystem.FLOOD_AND_DRAIN
            )
            controller = Controller.objects.create(
                farm=farm,
                controller_type=Controller.SENSOR_CONTROLLER,
                wifi_mac_address="00:11:22:33:44:55",
            )

        self.assertEqual(farm.created_at, mocked_now)
        self.assertEqual(farm.modified_at, mocked_now)
        self.assertEqual(coordinator.created_at, mocked_now)
        self.assertEqual(coordinator.modified_at, mocked_now)
        self.assertEqual(hydroponic_system.created_at, mocked_now)
        self.assertEqual(hydroponic_system.modified_at, mocked_now)
        self.assertEqual(controller.created_at, mocked_now)
        self.assertEqual(controller.modified_at, mocked_now)

        mocked_later = mocked_now + timedelta(hours=1)
        with mock.patch("django.utils.timezone.now", return_value=mocked_later):
            farm.name = "New name"
            farm.save()
            coordinator.local_ip_address = "192.168.0.2"
            coordinator.save()
            hydroponic_system.name = "A Flood and drain system"
            hydroponic_system.save()
            controller.wifi_mac_address = "11:22:33:44:55:66"
            controller.save()

        self.assertEqual(farm.created_at, mocked_now)
        self.assertEqual(farm.modified_at, mocked_later)
        self.assertEqual(coordinator.created_at, mocked_now)
        self.assertEqual(coordinator.modified_at, mocked_later)
        self.assertEqual(hydroponic_system.created_at, mocked_now)
        self.assertEqual(hydroponic_system.modified_at, mocked_later)
        self.assertEqual(controller.created_at, mocked_now)
        self.assertEqual(controller.modified_at, mocked_later)

    def test_controller_registration_flow(self):
        """Test a new controller automatically registering itself and being assigned to a farm."""

        farm = Farm.objects.create(name="ProtoFarm")
        coordinator = Coordinator.objects.create(
            farm=farm, local_ip_address="192.168.0.2", external_ip_address="3.3.3.3"
        )
        controller_a = Controller.objects.create(
            wifi_mac_address="00:11:22:33:44:55", external_ip_address="3.3.3.3"
        )
        controller_b = Controller.objects.create(
            wifi_mac_address="00:11:22:33:44:56", external_ip_address="3.3.3.3"
        )

        unregistered_controllers = Controller.objects.get_local_unregistered_controllers(
            coordinator.external_ip_address
        )
        self.assertIn(controller_a, unregistered_controllers)
        self.assertIn(controller_b, unregistered_controllers)

        controller_a.farm = farm
        controller_a.save()
        updated_unregistered_controllers = Controller.objects.get_local_unregistered_controllers(
            coordinator.external_ip_address
        )
        self.assertNotIn(controller_a, updated_unregistered_controllers)

