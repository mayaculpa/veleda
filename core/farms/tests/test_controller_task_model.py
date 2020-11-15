import uuid

from django.test import TestCase
from django.contrib.auth import get_user_model

from farms.models import (
    ControllerTask,
    ControllerComponent,
    ControllerComponentType,
    SiteEntity,
    Site,
)


class ControllerTaskTests(TestCase):
    """General controller task tests"""

    def setUp(self):
        self.controller_a = ControllerComponent.objects.create(
            component_type=ControllerComponentType.objects.create(name="TypeA"),
            site_entity=SiteEntity.objects.create(
                name="ControllerA",
                site=Site.objects.create(
                    name="SiteA",
                    owner=get_user_model().objects.create_user(
                        email="owner@bar.com", password="foo"
                    ),
                ),
            ),
        )

    def test_from_commands(self):
        """Test that commands can be parsed"""

        task_c = ControllerTask.objects.create(
            task_type=ControllerTask.READ_SENSOR_TYPE,
            controller_component=self.controller_a,
        )
        task_d = ControllerTask.objects.create(
            task_type=ControllerTask.WRITE_ACTUATOR_TYPE,
            controller_component=self.controller_a,
        )

        commands = {
            "start": [
                {
                    "uuid": str(uuid.uuid4()),
                    "type": ControllerTask.POLL_SENSOR_TYPE,
                    "foo": "bar",
                },
                {
                    "uuid": str(uuid.uuid4()),
                    "type": ControllerTask.SET_LIGHT_TYPE,
                    "hi": "there",
                },
            ],
            "stop": [{"uuid": str(task_c.id)}, {"uuid": str(task_d.id)}],
        }
        tasks = ControllerTask.objects.from_commands(commands, self.controller_a)

        task_a = [
            task for task in tasks if str(task.id) == commands["start"][0]["uuid"]
        ][0]
        task_b = [
            task for task in tasks if str(task.id) == commands["start"][1]["uuid"]
        ][0]
        self.assertEqual(task_a.task_type, commands["start"][0]["type"])
        self.assertEqual(task_a.controller_component_id, self.controller_a.id)
        self.assertEqual(task_a.state, ControllerTask.STARTING_STATE)
        self.assertEqual(task_a.parameters["foo"], commands["start"][0]["foo"])
        self.assertEqual(task_b.task_type, commands["start"][1]["type"])
        self.assertEqual(task_b.controller_component_id, self.controller_a.id)
        self.assertEqual(task_b.state, ControllerTask.STARTING_STATE)
        self.assertEqual(task_b.parameters["hi"], commands["start"][1]["hi"])

    def test_from_start_commands_errors(self):
        """Test the validation of the input data for start commands"""

        # Test uuid key check
        with self.assertRaisesMessage(ValueError, "uuid"):
            ControllerTask.objects.from_start_commands(
                start_commands=[{"type": ControllerTask.READ_SENSOR_TYPE}],
                controller=self.controller_a,
            )
        # Test type key check
        with self.assertRaisesMessage(ValueError, "type"):
            ControllerTask.objects.from_start_commands(
                start_commands=[{"uuid": str(uuid.uuid4())}],
                controller=self.controller_a,
            )
        # Test uuid validity check
        with self.assertRaisesMessage(ValueError, "UUID"):
            ControllerTask.objects.from_start_commands(
                start_commands=[
                    {
                        "uuid": "bar",
                        "type": ControllerTask.READ_SENSOR_TYPE,
                    }
                ],
                controller=self.controller_a,
            )
        # Test type validity check
        with self.assertRaisesMessage(ValueError, "type"):
            ControllerTask.objects.from_start_commands(
                start_commands=[{"uuid": str(uuid.uuid4()), "type": "foo"}],
                controller=self.controller_a,
            )
        # Test integrity check
        with self.assertRaisesMessage(ValueError, "Integrity"):
            task_a = ControllerTask.objects.create(
                task_type=ControllerTask.READ_SENSOR_TYPE,
                controller_component=self.controller_a,
            )
            ControllerTask.objects.from_start_commands(
                start_commands=[
                    {"uuid": str(task_a.id), "type": ControllerTask.READ_SENSOR_TYPE}
                ],
                controller=self.controller_a,
            )

    def test_from_stop_commands_errors(self):
        """Test the input validation for stop commands"""

        # Check that the UUID has to be given
        with self.assertRaisesMessage(ValueError, "uuid"):
            ControllerTask.objects.from_stop_commands([{"foo": "bar"}])

        # Check that only stoppable tasks are marked as stopping
        task_stopped = ControllerTask.objects.create(
            task_type=ControllerTask.READ_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STOPPED_STATE,
        )
        self.assertNotIn(task_stopped.state, ControllerTask.STOPPABLE_STATES)
        task_started = ControllerTask.objects.create(
            task_type=ControllerTask.READ_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
        )
        tasks = ControllerTask.objects.from_stop_commands(
            [{"uuid": str(task_stopped.id)}, {"uuid": str(task_started.id)}]
        )
        self.assertIn(task_started.id, [task.id for task in tasks])
        self.assertNotIn(task_stopped.id, [task.id for task in tasks])

    def test_to_commands(self):
        """Test the to_commands method used to generate necessary commands"""

        starting_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
            parameters={"foo": "bar"},
        )
        stopping_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STOPPING_STATE,
        )
        running_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.RUNNING_STATE,
        )

        tasks = [starting_task, stopping_task, running_task]
        commands = ControllerTask.to_commands(tasks)
        start_uuids = [command["uuid"] for command in commands["start"]]
        stop_uuids = [command["uuid"] for command in commands["stop"]]
        self.assertIn(str(starting_task.id), start_uuids)
        self.assertNotIn(str(starting_task.id), stop_uuids)
        self.assertIn(str(stopping_task.id), stop_uuids)
        self.assertNotIn(str(stopping_task.id), start_uuids)
        self.assertNotIn(str(running_task.id), start_uuids)
        self.assertNotIn(str(running_task.id), stop_uuids)

        command = starting_task.to_start_command()
        self.assertEqual(str(starting_task.id), command["uuid"])
        self.assertEqual(starting_task.task_type, command["type"])
        self.assertEqual(starting_task.parameters["foo"], command["foo"])
        self.assertFalse(starting_task.to_stop_command())

        command = stopping_task.to_stop_command()
        self.assertEqual(str(stopping_task.id), command["uuid"])
        self.assertFalse(stopping_task.to_start_command())

    def test_from_results(self):
        """Test the handling of results"""

        starting_task_a = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
        )
        starting_task_b = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
        )
        starting_task_c = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
        )
        stopping_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STOPPING_STATE,
        )
        running_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.RUNNING_STATE,
        )

        self.assertFalse(ControllerTask.objects.from_results({"foo": "bar"}))
        with self.assertRaisesMessage(ValueError, "uuid"):
            ControllerTask.objects.from_results({"start": [{"foo": "bar"}]})

        results = {
            "start": [
                {"uuid": str(starting_task_a.id), "status": "success"},
                {"uuid": str(starting_task_b.id), "status": "fail"},
            ],
            "stop": [
                {"uuid": str(stopping_task.id), "status": "success"},
                {"uuid": str(running_task.id), "status": "success"},
                {"uuid": str(starting_task_c.id), "status": "success"},
            ],
        }
        tasks = ControllerTask.objects.from_results(results)
        self.assertEqual(
            [task for task in tasks if task.id == starting_task_a.id][0].state,
            ControllerTask.RUNNING_STATE,
        )
        self.assertEqual(
            [task for task in tasks if task.id == starting_task_b.id][0].state,
            ControllerTask.FAILED_STATE,
        )
        self.assertEqual(
            [task for task in tasks if task.id == starting_task_c.id][0].state,
            ControllerTask.STOPPED_STATE,
        )
        self.assertEqual(
            [task for task in tasks if task.id == stopping_task.id][0].state,
            ControllerTask.STOPPED_STATE,
        )
        self.assertEqual(
            [task for task in tasks if task.id == running_task.id][0].state,
            ControllerTask.STOPPED_STATE,
        )

    def test_from_results_errors(self):
        """Test the error handling of handling task results"""

        task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
        )
        with self.assertRaisesMessage(ValueError, "status"):
            task.apply_start_result({"foo": "bar"})
        with self.assertRaisesMessage(ValueError, "status"):
            task.apply_stop_result({"foo": "bar"})

        # Check handling of invalid transitions for start results
        for state in [
            task.RUNNING_STATE,
            task.STOPPING_STATE,
            task.FAILED_STATE,
            task.STOPPED_STATE,
        ]:
            task.state = state
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_start_result({"status": "success"})
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_start_result({"status": "fail"})

        # Check handling of invalid transitions for stop results
        for state in [task.STOPPED_STATE, task.FAILED_STATE]:
            task.state = state
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_stop_result({"status": "success"})
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_stop_result({"status": "fail"})

    def test_commands_from_register(self):
        """Test the commands that are generated from a registration request"""

        starting_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
        )
        running_task_a = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.RUNNING_STATE,
        )
        running_task_b = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.RUNNING_STATE,
        )
        stopping_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STOPPING_STATE,
        )
        stopped_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STOPPED_STATE,
        )
        failed_task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.FAILED_STATE,
        )
        started_tasks = [str(running_task_b.id)]

        commands = ControllerTask.objects.commands_from_register(
            started_tasks, self.controller_a.id
        )
        start_uuids = [task["uuid"] for task in commands.get("start", [])]
        self.assertIn(str(starting_task.id), start_uuids)
        self.assertIn(str(running_task_a.id), start_uuids)
        self.assertNotIn(str(running_task_b.id), start_uuids)
        self.assertNotIn(str(stopping_task.id), start_uuids)
        self.assertNotIn(str(stopped_task.id), start_uuids)
        self.assertNotIn(str(failed_task.id), start_uuids)

    def test_to_string(self):
        """Test the to string method"""

        task = ControllerTask.objects.create(
            task_type=ControllerTask.POLL_SENSOR_TYPE,
            controller_component=self.controller_a,
            state=ControllerTask.STARTING_STATE,
        )
        self.assertIn(task.task_type, str(task))
        self.assertIn(task.state, str(task))
