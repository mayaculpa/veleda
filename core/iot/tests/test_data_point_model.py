from datetime import datetime, timezone, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime

from iot.models import (
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
            peripheral_type=PeripheralComponent.PeripheralType.BME280_SENSOR.value,
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
        data_point.time = datetime.now().strftime("%s")
        self.assertRaises(ValueError, data_point.save)
        data_point.time = int(datetime.now().strftime("%s"))
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
        data["time"] = datetime.now().strftime("%s")
        self.assertRaises(ValueError, DataPoint.objects.from_telemetry, data)
        data["time"] = int(datetime.now().strftime("%s"))
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


class DataPointAggregationTests(TestCase):
    """General data point model tests"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email="owner@bar.com", password="foo"
        )

        self.site = Site.objects.create(name="Site A", owner=self.owner)
        self.controller = ControllerComponent.objects.create(
            component_type=ControllerComponentType.objects.create(name="ESP32"),
            site_entity=SiteEntity.objects.create(name="SomeESP32", site=self.site),
        )
        self.peripheral_a = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.ANALOG_IN,
            site_entity=SiteEntity.objects.create(name="PeriA", site=self.site),
            controller_component=self.controller,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.peripheral_b = PeripheralComponent.objects.create(
            peripheral_type=PeripheralComponent.PeripheralType.ANALOG_IN,
            site_entity=SiteEntity.objects.create(name="PeriB", site=self.site),
            controller_component=self.controller,
            state=PeripheralComponent.State.ADDED,
            other_parameters={},
        )
        self.data_point_type_a = DataPointType.objects.create(name="dptA", unit="uA")
        self.data_point_type_b = DataPointType.objects.create(name="dptB", unit="uB")
        data_points_a = []
        data_points_b = []
        self.now = datetime.now(tz=timezone.utc)
        for day in range(5):
            for point in range(50):
                dp_time = self.now.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=day, minutes=point * 20)
                value = (1 + day) * (1 + point) - 1
                data_points_a.append(
                    DataPoint(
                        peripheral_component=self.peripheral_a,
                        data_point_type=self.data_point_type_a,
                        value=value,
                        time=dp_time,
                    )
                )
                data_points_b.append(
                    DataPoint(
                        peripheral_component=self.peripheral_b,
                        data_point_type=self.data_point_type_b,
                        value=value * 2,
                        time=dp_time + timedelta(seconds=1),
                    )
                )
        DataPoint.objects.bulk_create(data_points_a)
        DataPoint.objects.bulk_create(data_points_b)

    def test_data_point_aggregation_day(self):
        """Test data point aggregation by day."""

        # Peripheral A
        data_points = DataPoint.objects.by_day(
            peripheral_component_id=self.peripheral_a.pk,
            data_point_type_id=self.data_point_type_a.pk,
            from_date=self.now.date(),
            before_date=self.now.date() + timedelta(days=3),
        )
        day_one = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Ensure descending order of data points (newest to oldest)
        day_one_dps = data_points[2]
        self.assertEqual(day_one_dps["day"], day_one)
        self.assertEqual(day_one_dps["avg"], 24.5)
        self.assertEqual(day_one_dps["min"], 0.0)
        self.assertEqual(day_one_dps["max"], 49.0)

        day_three_dps = data_points[0]
        self.assertEqual(day_three_dps["day"], day_one + timedelta(days=2))
        self.assertEqual(day_three_dps["avg"], 75.5)
        self.assertEqual(day_three_dps["min"], 2.0)
        self.assertEqual(day_three_dps["max"], 149.0)

        # Peripheral B
        data_points = DataPoint.objects.by_day(
            peripheral_component_id=self.peripheral_b.pk,
            data_point_type_id=self.data_point_type_b.pk,
            from_date=self.now.date(),
            before_date=self.now.date() + timedelta(days=3),
        )
        day_three_dps = data_points[0]
        self.assertEqual(day_three_dps["day"], day_one + timedelta(days=2))
        self.assertEqual(day_three_dps["avg"], 151.0)
        self.assertEqual(day_three_dps["min"], 4.0)
        self.assertEqual(day_three_dps["max"], 298.0)

    def test_data_point_aggregation_hour(self):
        """Test data point aggregation by hour method."""

        # Peripheral A
        hour_one = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        hour_ten = hour_one + timedelta(hours=9)
        data_points = DataPoint.objects.by_hour(
            peripheral_component_id=self.peripheral_a.pk,
            data_point_type_id=self.data_point_type_a.pk,
            from_time=hour_one,
            before_time=hour_one + timedelta(hours=10),
        )
        # Ensure that the data is returned from newest to oldest
        hour_one_dps = list(data_points)[-1]
        self.assertEqual(hour_one_dps["time_hour"], hour_one)
        self.assertEqual(hour_one_dps["avg"], 1.0)
        self.assertEqual(hour_one_dps["min"], 0.0)
        self.assertEqual(hour_one_dps["max"], 2.0)
        hour_ten_dps = data_points[0]
        self.assertEqual(hour_ten_dps["time_hour"], hour_ten)
        self.assertEqual(hour_ten_dps["avg"], 28.0)
        self.assertEqual(hour_ten_dps["min"], 27.0)
        self.assertEqual(hour_ten_dps["max"], 29.0)

        # Peripheral B
        data_points = DataPoint.objects.by_hour(
            peripheral_component_id=self.peripheral_b.pk,
            data_point_type_id=self.data_point_type_b.pk,
            from_time=hour_one,
            before_time=hour_one + timedelta(hours=10),
        )
        hour_one_dps = list(data_points)[-1]
        self.assertEqual(hour_one_dps["time_hour"], hour_one)
        self.assertEqual(hour_one_dps["avg"], 2.0)
        self.assertEqual(hour_one_dps["min"], 0.0)
        self.assertEqual(hour_one_dps["max"], 4.0)
        hour_ten_dps = data_points[0]
        self.assertEqual(hour_ten_dps["time_hour"], hour_ten)
        self.assertEqual(hour_ten_dps["avg"], 56.0)
        self.assertEqual(hour_ten_dps["min"], 54.0)
        self.assertEqual(hour_ten_dps["max"], 58.0)