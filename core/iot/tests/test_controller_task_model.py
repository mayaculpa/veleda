import uuid

from django.test import TestCase
from django.contrib.auth import get_user_model

from iot.models import (
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
            task_type=ControllerTask.TaskType.READ_SENSOR,
            controller_component=self.controller_a,
        )
        task_d = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.SET_VALUE,
            controller_component=self.controller_a,
        )

        commands = {
            "start": [
                {
                    "uuid": str(uuid.uuid4()),
                    "type": ControllerTask.TaskType.POLL_SENSOR,
                    "foo": "bar",
                },
                {
                    "uuid": str(uuid.uuid4()),
                    "type": ControllerTask.TaskType.SET_RGB_LED,
                    "hi": "there",
                },
            ],
            "stop": [{"uuid": str(task_c.pk)}, {"uuid": str(task_d.pk)}],
        }
        tasks = ControllerTask.objects.from_commands(commands, self.controller_a)

        task_a = [
            task for task in tasks if str(task.pk) == commands["start"][0]["uuid"]
        ][0]
        task_b = [
            task for task in tasks if str(task.pk) == commands["start"][1]["uuid"]
        ][0]
        self.assertEqual(task_a.task_type, commands["start"][0]["type"])
        self.assertEqual(task_a.controller_component_id, self.controller_a.pk)
        self.assertEqual(task_a.state, ControllerTask.State.STARTING)
        self.assertEqual(task_a.parameters["foo"], commands["start"][0]["foo"])
        self.assertEqual(task_b.task_type, commands["start"][1]["type"])
        self.assertEqual(task_b.controller_component_id, self.controller_a.pk)
        self.assertEqual(task_b.state, ControllerTask.State.STARTING)
        self.assertEqual(task_b.parameters["hi"], commands["start"][1]["hi"])

    def test_from_start_commands_errors(self):
        """Test the validation of the input data for start commands"""

        # Test uuid key check
        with self.assertRaisesMessage(ValueError, "uuid"):
            ControllerTask.objects.from_start_commands(
                start_commands=[{"type": ControllerTask.TaskType.READ_SENSOR}],
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
                        "type": ControllerTask.TaskType.READ_SENSOR,
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
                task_type=ControllerTask.TaskType.READ_SENSOR,
                controller_component=self.controller_a,
            )
            ControllerTask.objects.from_start_commands(
                start_commands=[
                    {"uuid": str(task_a.pk), "type": ControllerTask.TaskType.READ_SENSOR}
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
            task_type=ControllerTask.TaskType.READ_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STOPPED,
        )
        self.assertNotIn(task_stopped.state, ControllerTask.STOPPABLE_STATES)
        task_started = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.READ_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
        )
        tasks = ControllerTask.objects.from_stop_commands(
            [{"uuid": str(task_stopped.pk)}, {"uuid": str(task_started.pk)}]
        )
        self.assertIn(task_started.pk, [task.pk for task in tasks])
        self.assertNotIn(task_stopped.pk, [task.pk for task in tasks])

    def test_to_commands(self):
        """Test the to_commands method used to generate necessary commands"""

        starting_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
            parameters={"foo": "bar"},
        )
        stopping_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STOPPING,
        )
        running_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.RUNNING,
        )

        tasks = [starting_task, stopping_task, running_task]
        commands = ControllerTask.objects.to_commands(tasks)
        start_uuids = [command["uuid"] for command in commands["start"]]
        stop_uuids = [command["uuid"] for command in commands["stop"]]
        self.assertIn(str(starting_task.pk), start_uuids)
        self.assertNotIn(str(starting_task.pk), stop_uuids)
        self.assertIn(str(stopping_task.pk), stop_uuids)
        self.assertNotIn(str(stopping_task.pk), start_uuids)
        self.assertNotIn(str(running_task.pk), start_uuids)
        self.assertNotIn(str(running_task.pk), stop_uuids)

        command = starting_task.to_start_command()
        self.assertEqual(str(starting_task.pk), command["uuid"])
        self.assertEqual(starting_task.task_type, command["type"])
        self.assertEqual(starting_task.parameters["foo"], command["foo"])
        self.assertFalse(starting_task.to_stop_command())

        command = stopping_task.to_stop_command()
        self.assertEqual(str(stopping_task.pk), command["uuid"])
        self.assertFalse(stopping_task.to_start_command())

    def test_from_results(self):
        """Test the handling of results"""

        starting_task_a = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
        )
        starting_task_b = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
        )
        starting_task_c = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
        )
        stopping_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STOPPING,
        )
        running_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.RUNNING,
        )

        self.assertFalse(ControllerTask.objects.from_results({"foo": "bar"}))
        with self.assertRaisesMessage(ValueError, "uuid"):
            ControllerTask.objects.from_results({"start": [{"foo": "bar"}]})

        results = {
            "start": [
                {"uuid": str(starting_task_a.pk), "status": "success"},
                {"uuid": str(starting_task_b.pk), "status": "fail"},
            ],
            "stop": [
                {"uuid": str(stopping_task.pk), "status": "success"},
                {"uuid": str(running_task.pk), "status": "success"},
                {"uuid": str(starting_task_c.pk), "status": "success"},
            ],
        }
        tasks = ControllerTask.objects.from_results(results)
        self.assertEqual(
            [task for task in tasks if task.pk == starting_task_a.pk][0].state,
            ControllerTask.State.RUNNING,
        )
        self.assertEqual(
            [task for task in tasks if task.pk == starting_task_b.pk][0].state,
            ControllerTask.State.FAILED,
        )
        self.assertEqual(
            [task for task in tasks if task.pk == starting_task_c.pk][0].state,
            ControllerTask.State.STOPPED,
        )
        self.assertEqual(
            [task for task in tasks if task.pk == stopping_task.pk][0].state,
            ControllerTask.State.STOPPED,
        )
        self.assertEqual(
            [task for task in tasks if task.pk == running_task.pk][0].state,
            ControllerTask.State.STOPPED,
        )

    def test_from_results_errors(self):
        """Test the error handling of handling task results"""

        task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
        )
        with self.assertRaisesMessage(ValueError, "status"):
            task.apply_start_result({"foo": "bar"})
        with self.assertRaisesMessage(ValueError, "status"):
            task.apply_stop_result({"foo": "bar"})

        # Check handling of invalid transitions for start results
        for state in [
            task.State.RUNNING,
            task.State.STOPPING,
            task.State.FAILED,
            task.State.STOPPED,
        ]:
            task.state = state
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_start_result({"status": "success"})
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_start_result({"status": "fail"})

        # Check handling of invalid transitions for stop results
        for state in [task.State.STOPPED, task.State.FAILED]:
            task.state = state
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_stop_result({"status": "success"})
            with self.assertRaises(ControllerTask.InvalidTransition):
                task.apply_stop_result({"status": "fail"})

    def test_commands_from_register(self):
        """Test the commands that are generated from a registration request"""

        starting_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
        )
        running_task_a = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.RUNNING,
        )
        running_task_b = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.RUNNING,
        )
        stopping_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STOPPING,
        )
        stopped_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STOPPED,
        )
        failed_task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.FAILED,
        )
        started_tasks = [str(running_task_b.pk)]

        commands = ControllerTask.objects.commands_from_register(
            started_tasks, self.controller_a.pk
        )
        start_uuids = [task["uuid"] for task in commands.get("start", [])]
        self.assertIn(str(starting_task.pk), start_uuids)
        self.assertIn(str(running_task_a.pk), start_uuids)
        self.assertNotIn(str(running_task_b.pk), start_uuids)
        self.assertNotIn(str(stopping_task.pk), start_uuids)
        self.assertNotIn(str(stopped_task.pk), start_uuids)
        self.assertNotIn(str(failed_task.pk), start_uuids)

    def test_to_string(self):
        """Test the to string method"""

        task = ControllerTask.objects.create(
            task_type=ControllerTask.TaskType.POLL_SENSOR,
            controller_component=self.controller_a,
            state=ControllerTask.State.STARTING,
        )
        self.assertIn(task.task_type, str(task))
        self.assertIn(task.state, str(task))
