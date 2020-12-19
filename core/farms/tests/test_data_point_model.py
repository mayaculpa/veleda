import uuid
from datetime import datetime, timezone, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime

from farms.models import (
    ControllerComponent,
    ControllerComponentType,
    DataPoint,
    DataPointType,
    PeripheralComponent,
    Site,
    SiteEntity,
)


class DataPointTests(TestCase):
    """General data point model tests"""

    def setUp(self):
        self.site_a = Site.objects.create(
            name="Site A",
            owner=get_user_model().objects.create_user(
                email="owner@bar.com",
                password="foo",
            ),
        )
        self.esp32_type = ControllerComponentType.objects.create(name="ESP32")
        self.esp32_a_controller = ControllerComponent.objects.create(
            component_type=self.esp32_type,
            site_entity=SiteEntity.objects.create(name="ESP32 A", site=self.site_a),
        )
        self.bme280_a = PeripheralComponent.objects.create(
            site_entity=SiteEntity.objects.create(name="BME280 A", site=self.site_a),
            peripheral_type=PeripheralComponent.BME280_TYPE,
            controller_component=self.esp32_a_controller,
        )
        self.air_temperature = DataPointType.objects.create(name="Air Temp", unit="°C")
        self.air_pressure = DataPointType.objects.create(name="Air Pressure", unit="Pa")

    def test_create_timestamp_smearing(self):
        """Tests that data points with the same timestamp are handled correctly"""

        time_a = datetime.now(tz=timezone.utc)
        data_point_a = DataPoint.objects.create(
            time=time_a,
            value=22,
            peripheral_component=self.bme280_a,
            data_point_type=self.air_temperature,
        )
        data_point_b = DataPoint.objects.create(
            time=time_a,
            value=23,
            peripheral_component=self.bme280_a,
            data_point_type=self.air_temperature,
        )
        self.assertEqual(data_point_a.time, time_a)
        self.assertGreater(data_point_b.time, time_a)

    def test_create_from_telemetry(self):
        """Test creating data points from a telemetry message"""

        data = {
            "peripheral": str(self.bme280_a.pk),
            "time": datetime.now(tz=timezone.utc),
            "data_points": [
                {"value": 30, "data_point_type": str(self.air_temperature.id)},
                {"value": 101000, "data_point_type": str(self.air_pressure.id)},
            ],
        }
        data_points = DataPoint.objects.from_telemetry(data)
        temperature_data_point = [
            data_point
            for data_point in data_points
            if data_point.data_point_type_id == str(self.air_temperature.id)
        ][0]
        pressure_data_point = [
            data_point
            for data_point in data_points
            if data_point.data_point_type_id == str(self.air_pressure.id)
        ][0]

        self.assertEqual(temperature_data_point.value, 30)
        self.assertEqual(pressure_data_point.value, 101000)
        time_difference = abs(pressure_data_point.time - temperature_data_point.time)
        self.assertEqual(time_difference, timedelta(microseconds=1))
        self.assertLessEqual(
            pressure_data_point.time, data["time"] + timedelta(microseconds=2)
        )
        self.assertGreaterEqual(
            pressure_data_point.time, data["time"] - timedelta(microseconds=2)
        )

    def test_telemetry_without_timestamp(self):
        """Test that telemetry without a timestamp uses the current time"""

        data = {
            "peripheral": str(self.bme280_a.pk),
            "data_points": [
                {"value": 30, "data_point_type": str(self.air_temperature.id)},
                {"value": 101000, "data_point_type": str(self.air_pressure.id)},
            ],
        }
        data_points = DataPoint.objects.from_telemetry(data)
        temperature_data_point = [
            data_point
            for data_point in data_points
            if data_point.data_point_type_id == str(self.air_temperature.id)
        ][0]
        pressure_data_point = [
            data_point
            for data_point in data_points
            if data_point.data_point_type_id == str(self.air_pressure.id)
        ][0]

        # Check that both data points were saved and the timestamps are smeared
        self.assertEqual(temperature_data_point.value, 30)
        self.assertEqual(pressure_data_point.value, 101000)
        time_difference = abs(pressure_data_point.time - temperature_data_point.time)
        self.assertEqual(time_difference, timedelta(microseconds=1))

        # Ensure that the timestamp is within a reasonable range from now
        time_difference = abs(pressure_data_point.time - datetime.now(tz=timezone.utc))
        self.assertLess(time_difference, timedelta(seconds=30))

    def test_telemetry_with_text_timestamp(self):
        """Test that telemetry with a string timestamp works"""

        data = {
            "peripheral": str(self.bme280_a.pk),
            "time": str(datetime.now(tz=timezone.utc)),
            "data_points": [
                {"value": 30, "data_point_type": str(self.air_temperature.id)},
                {"value": 101000, "data_point_type": str(self.air_pressure.id)},
            ],
        }
        data_points = DataPoint.objects.from_telemetry(data)
        temperature_data_point = [
            data_point
            for data_point in data_points
            if data_point.data_point_type_id == str(self.air_temperature.id)
        ][0]
        pressure_data_point = [
            data_point
            for data_point in data_points
            if data_point.data_point_type_id == str(self.air_pressure.id)
        ][0]

        # Check that both data points were saved and the timestamps are smeared
        self.assertEqual(temperature_data_point.value, 30)
        self.assertEqual(pressure_data_point.value, 101000)
        time_difference = abs(pressure_data_point.time - temperature_data_point.time)
        self.assertEqual(time_difference, timedelta(microseconds=1))

        # Ensure that the timestamp is within a reasonable range from now
        time_difference = abs(pressure_data_point.time - parse_datetime(data["time"]))
        self.assertLess(time_difference, timedelta(seconds=30))

    def test_naive_time_save(self):
        """Test that naive timestamps are not accepted"""

        # Check naive datetimes
        data_point = DataPoint(
            time=datetime.now(),
            value=22,
            peripheral_component=self.bme280_a,
            data_point_type=self.air_temperature,
        )
        self.assertRaises(ValueError, data_point.save)

        # Check str, unix and int date types
        data_point.time = str(datetime.now())
        self.assertRaises(ValueError, data_point.save)
        data_point.time = datetime.now().strftime('%s')
        self.assertRaises(ValueError, data_point.save)
        data_point.time = int(datetime.now().strftime('%s'))
        self.assertRaises(ValueError, data_point.save)
        
    def test_invalid_time_from_telemetry(self):
        """Test that invalid time is also checked by from telemetry"""

        data = {
            "peripheral": str(self.bme280_a.pk),
            "time": datetime.now(),
            "data_points": [
                {"value": 30, "data_point_type": str(self.air_temperature.id)},
                {"value": 101000, "data_point_type": str(self.air_pressure.id)},
            ],
        }
        self.assertRaises(ValueError, DataPoint.objects.from_telemetry, data)

        # Check str, unix and int date types
        data["time"] = str(datetime.now())
        self.assertRaises(ValueError, DataPoint.objects.from_telemetry, data)
        data["time"] = datetime.now().strftime('%s')
        self.assertRaises(ValueError, DataPoint.objects.from_telemetry, data)
        data["time"] = int(datetime.now().strftime('%s'))
        self.assertRaises(ValueError, DataPoint.objects.from_telemetry, data)
        data["time"] = ""
        self.assertRaises(ValueError, DataPoint.objects.from_telemetry, data)


    def test_to_string(self):
        """Test that the string representation contains the value"""

        data_point = DataPoint(
            time=datetime.now(),
            value=22,
            peripheral_component=self.bme280_a,
            data_point_type=self.air_temperature,
        )
        self.assertIn(str(data_point.value), str(data_point))

        data_point_type = DataPointType(name="Some name", unit="Some unit")
        self.assertIn(data_point_type.name, str(data_point_type))
