from iot.models.controller import ControllerAuthToken, ControllerMessage
from django.contrib.auth import get_user_model
from django.test import TestCase

from iot.models import ControllerComponentType, ControllerComponent, Site, SiteEntity


class TestControllerComponent(TestCase):
    def setUp(self):
        self.site_a = Site.objects.create(
            name="Site A",
            owner=get_user_model().objects.create_user(
                email="owner@bar.com",
                password="foo",
            ),
        )
        self.esp32_a_entity = SiteEntity.objects.create(
            name="ESP32 A", site=self.site_a
        )
        self.esp32_type = ControllerComponentType.objects.create(name="ESP32")
        self.esp32_a_controller = ControllerComponent.objects.create(
            component_type=self.esp32_type,
            site_entity=self.esp32_a_entity,
        )

    def test_string_representation(self):
        """Test how objects are converted to strings"""

        name = "hi there"
        controller_component_type = ControllerComponentType(name=name)
        self.assertIn(name, str(controller_component_type))

        self.assertIn(self.esp32_a_entity.name, str(self.esp32_a_controller))

        controller_auth_token = ControllerAuthToken(controller=self.esp32_a_controller)
        self.assertIn(self.esp32_a_entity.name, str(controller_auth_token))

    def test_controller_message_types(self):
        message = ControllerMessage(
            controller=self.esp32_a_controller, message={"type": "cmd"}
        )
        self.assertTrue(message.is_command_type())
        message = ControllerMessage(
            controller=self.esp32_a_controller, message={"type": "reg"}
        )
        self.assertTrue(message.is_register_type())
        message = ControllerMessage(
            controller=self.esp32_a_controller, message={"type": "result"}
        )
        self.assertTrue(message.is_result_type())
        message = ControllerMessage(
            controller=self.esp32_a_controller, message={"type": "sys"}
        )
        self.assertTrue(message.is_system_type())

    def test_controller_message_extraction(self):
        some_command = {"foo": "bar", "hi": 22}
        message = ControllerMessage(
            controller=self.esp32_a_controller,
            message={"type": "tele", "peripheral": some_command},
        )
        self.assertFalse(message.to_peripheral_commands())
        message.message["type"] = "cmd"
        self.assertEqual(some_command, message.to_peripheral_commands())
        self.assertFalse(message.to_peripheral_results())

        message = ControllerMessage(
            controller=self.esp32_a_controller,
            message={"type": "tele", "task": some_command},
        )
        self.assertFalse(message.to_task_commands())
        message.message["type"] = "cmd"
        self.assertEqual(some_command, message.to_task_commands())
        self.assertFalse(message.to_task_results())

        message = ControllerMessage(
            controller=self.esp32_a_controller,
            message={"type": "tel", "jo": some_command},
        )
        self.assertEqual({"type": "tel", "jo": some_command}, message.to_telemetry())

        message = ControllerMessage(
            controller=self.esp32_a_controller,
            message={"type": "tel", "jo": some_command},
        )
        self.assertEqual("tel", message.get_type())

        some_types = ["a", "b", "c"]
        message = ControllerMessage(
            controller=self.esp32_a_controller,
            message={"type": "tele", "peripherals": some_types},
        )
        self.assertFalse(message.to_peripheral_register())
        message.message["type"] = "reg"
        self.assertEqual(some_types, message.to_peripheral_register())

        message = ControllerMessage(
            controller=self.esp32_a_controller,
            message={"type": "tele", "tasks": some_types},
        )
        self.assertFalse(message.to_task_register())
        message.message["type"] = "reg"
        self.assertEqual(some_types, message.to_task_register())

    def test_message_creation(self):
        peripheral_commands = {"some": "command"}
        task_commands = {"other": "stuff"}
        request_id = "abcd"
        message = ControllerMessage.to_command_message(
            peripheral_commands=peripheral_commands,
            task_commands=task_commands,
            request_id=request_id,
        )

        self.assertEqual("cmd", message["type"])
        self.assertEqual(peripheral_commands, message["peripheral"])
        self.assertEqual(task_commands, message["task"])
        self.assertEqual(request_id, message["request_id"])
