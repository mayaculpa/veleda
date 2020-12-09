from asgiref.sync import async_to_sync
from datetime import datetime, timezone
from typing import Dict, List, Optional, Type
import uuid

from channels.layers import get_channel_layer
from channels.exceptions import InvalidChannelLayerError
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from farms.models.controller import ControllerComponent


class ControllerTaskManager(models.Manager):
    """Manages starting and stopping of tasks, in addition to CRUD methods. On select
    methods also handles sending the commands to the connected controller."""

    def start(
        self,
        controller_component_id: uuid.UUID,
        task_type: Type["ControllerTask.TaskType"],
        parameters: Dict,
        run_until: datetime = None,
    ) -> "ControllerTask":
        """Create and start a task on the specified controller"""

        with transaction.atomic():
            controller_task = self.select_related("controller_component").create(
                controller_component_id=controller_component_id,
                task_type=task_type,
                state=self.model.State.STARTING.value,
                parameters=parameters,
                run_until=run_until,
            )
            task_commands = self.model.to_commands([controller_task])
            self._send_controller_task_commands(
                controller_task.controller_component.channel_name, task_commands
            )
        return controller_task

    def restart(self, task_id: uuid.UUID) -> "ControllerTask":
        """Restart a stopped or failed task on a controller"""

        with transaction.atomic():
            controller_task = self.select_related("controller_component").get(
                pk=task_id
            )
            controller_task.state = self.model.State.STARTING
            controller_task.save()
            task_commands = self.model.to_commands([controller_task])
            self._send_controller_task_commands(
                controller_task.controller_component.channel_name, task_commands
            )
        return controller_task

    def stop(self, task_id: uuid.UUID) -> "ControllerTask":
        """Stop a task on a controller"""

        with transaction.atomic():
            controller_task = self.select_related("controller_component").get(
                pk=task_id
            )
            controller_task.state = self.model.State.STOPPING
            controller_task.save()
            task_commands = self.model.to_commands([controller_task])
            self._send_controller_task_commands(
                controller_task.controller_component.channel_name, task_commands
            )
        return controller_task

    def from_commands(self, task_commands, controller) -> List[Type["ControllerTask"]]:
        """Parse a command message to start tasks and get those to be stopped"""

        tasks: List[Type["ControllerTask"]] = []
        if task_commands:
            start_commands = task_commands.get("start")
            if start_commands:
                tasks.extend(self.from_start_commands(start_commands, controller))
            stop_commands = task_commands.get("stop")
            if stop_commands:
                tasks.extend(self.from_stop_commands(stop_commands))
        return tasks

    def from_start_commands(
        self, start_commands: List[Dict], controller
    ) -> List[Type["ControllerTask"]]:
        """Start tasks from the task start command after validating model fields."""

        tasks: List[Type["ControllerTask"]] = []
        for start_command in start_commands:
            command = start_command.copy()
            try:
                task_id = command.pop("uuid")
                task_type = command.pop("type")
                run_until = command.pop("run_until", None)
                if "duration_ms" in command:
                    raise ValueError(
                        "Use 'run_until' instead of 'duration_ms' for task running duration."
                    )
            except KeyError as err:
                if "task_id" in locals():
                    raise ValueError(f"Missing key {err} for {task_id}") from err
                raise ValueError(f"Missing key {err}") from err
            model = self.model(
                id=task_id,
                controller_component=controller,
                state=self.model.State.STARTING,
                task_type=task_type,
                run_until=run_until,
                parameters=command,
            )
            try:
                model.clean_fields()
            except ValidationError as err:
                raise ValueError(err) from err
            tasks.append(model)
        try:
            return self.bulk_create(tasks)
        except IntegrityError as err:
            # Handle errors regarding foreign keys
            raise ValueError(
                f"Integrity error: {str(err).split('DETAIL:  ',1)[1][:-1]}"
            ) from err

    def from_stop_commands(
        self, stop_commands: List[Dict]
    ) -> List[Type["ControllerTask"]]:
        """Request tasks to stop. Ignores tasks that cannot be stopped."""

        try:
            uuids = [command["uuid"] for command in stop_commands]
        except KeyError as err:
            raise ValueError(f"Missing key {err}") from err
        tasks = list(
            self.filter(id__in=uuids).filter(state__in=self.model.STOPPABLE_STATES)
        )
        for task in tasks:
            task.state = self.model.State.STOPPING
        self.bulk_update(tasks, ["state"])
        return tasks

    def from_results(self, results: Dict) -> List[Type["ControllerTask"]]:
        """Update states from results commands"""

        # Get all task ids to update
        try:
            uuids = [result["uuid"] for result in results.get("start", [])]
            uuids.extend([result["uuid"] for result in results.get("stop", [])])
        except KeyError as err:
            raise ValueError(f"Missing key {err}") from err
        tasks = self.select_for_update().filter(id__in=uuids)

        with transaction.atomic():
            for start_result in results.get("start", []):
                next(
                    task for task in tasks if str(task.id) == start_result["uuid"]
                ).apply_start_result(start_result)
            for stop_result in results.get("stop", []):
                next(
                    task for task in tasks if str(task.id) == stop_result["uuid"]
                ).apply_stop_result(stop_result)
            self.bulk_update(tasks, ["state"])
        return tasks

    def commands_from_register(
        self, running_tasks: List[str], controller_id: uuid.UUID
    ) -> Dict:
        """Updates tasks to be re-started to the starting state and returns commands to
        be re-start tasks on a controller. However, exclude the tasks that the
        controller reports to already be running."""

        tasks = (
            ControllerTask.objects.filter(controller_component__pk=controller_id)
            .filter(state__in=ControllerTask.RE_START_STATES)
            .exclude(pk__in=running_tasks)
            .select_for_update()
        )

        with transaction.atomic():
            for task in tasks:
                task.state = ControllerTask.State.STARTING
            self.bulk_update(tasks, ["state"])

        commands = []
        for task in tasks:
            commands.append(task.to_start_command())
        if commands:
            return {"start": commands}
        return {}

    @staticmethod
    def _send_controller_task_commands(
        channel_name: str, task_commands: List[Dict], request_id: str = None
    ):
        if not channel_name:
            raise ValueError("Controller has not connected to the server")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(
            channel_name,
            {
                "type": "send.controller.task.commands",
                "commands": task_commands,
                "request_id": request_id,
            },
        )


class ControllerTask(models.Model):
    """Tasks interacting with peripherals on controllers"""

    objects = ControllerTaskManager()

    class InvalidTransition(Exception):
        """Thrown when an invalid state change is applied"""

    class State(models.TextChoices):
        """Possible task states."""

        STARTING = ("starting", "Starting")
        RUNNING = ("running", "Running")
        STOPPING = ("stopping", "Stopping")
        FAILED = ("failed", "Failed")
        STOPPED = ("stopped", "Stopped")

    # States for which stop commands can be created
    STOPPABLE_STATES = [State.STARTING.value, State.RUNNING.value, State.STOPPING.value]
    # States to start tasks again (registration after reboot)
    RE_START_STATES = [State.STARTING.value, State.RUNNING.value]

    class TaskType(models.TextChoices):
        """Possible task types"""

        INVALID_TYPE = "InvalidType", "Invalid type"
        ALERT_SENSOR = "AlertSensor", "Alert sensor"
        POLL_SENSOR = "PollSensor", "Poll sensor"
        READ_SENSOR = "ReadSensor", "Read sensor"
        SET_LIGHT = "SetLight", "Set light"
        WRITE_ACTUATOR = "WriteActuator", "Write actuator"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    controller_component = models.ForeignKey(
        ControllerComponent,
        related_name="controller_task_set",
        on_delete=models.CASCADE,
        help_text="On which controller this task is executed.",
    )
    task_type = models.CharField(
        choices=TaskType.choices,
        max_length=64,
        help_text="The type of the task on the controller",
    )
    state = models.CharField(
        choices=State.choices,
        max_length=64,
        help_text="The state of the controller task.",
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="The setup parameters excl. the task's ID, state and type. The"
        "peripheral ID parameter has to use the peripheral component's ID instead that"
        "of its site entity.",
    )
    run_until = models.DateTimeField(
        blank=True, null=True, help_text="Until when the task should run."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The datetime of creation.",
    )
    modified_at = models.DateTimeField(
        auto_now=True, help_text="The datetime of the last update."
    )

    @classmethod
    def to_commands(cls, tasks: List[Type["ControllerTask"]]) -> Dict:
        """Convert a list of tasks to commands. Ignores tasks that cannot be converted
        to commands"""

        start_tasks = []
        stop_tasks = []
        for task in tasks:
            if command := task.to_start_command():
                start_tasks.append(command)
            if command := task.to_stop_command():
                stop_tasks.append(command)

        commands = {}
        if start_tasks:
            commands.update({"start": start_tasks})
        if stop_tasks:
            commands.update({"stop": stop_tasks})
        return commands

    def to_start_command(self) -> Optional[Dict]:
        """If in starting state, return a command that starts the task, else None"""

        if self.state == self.State.STARTING:
            if self.run_until:
                now = datetime.now(tz=timezone.utc)
                if self.run_until > now:
                    self.state = self.State.STOPPED
                    self.save()
                    return None
                return {
                    "uuid": str(self.id),
                    "type": self.task_type,
                    "duration_ms": (self.run_until - now).seconds(),
                }
            return {
                "uuid": str(self.id),
                "type": self.task_type,
                **self.parameters,
            }
        return None

    def to_stop_command(self) -> Optional[Dict]:
        """If in stopping state, return a command that stops the task, else None"""

        if self.state == self.State.STOPPING:
            return {"uuid": str(self.id)}
        return None

    def apply_start_result(self, result):
        """Modify the state according to the result. Raises ValueError or
        InvalidTransition on errors."""

        try:
            status = result["status"]
        except KeyError as err:
            raise ValueError(f"Missing key {err}") from err
        if self.state == self.State.STARTING and status == "success":
            self.state = self.State.RUNNING
        elif self.state == self.State.STARTING and status == "fail":
            self.state = self.State.FAILED
        else:
            raise self.InvalidTransition(f"Apply start result {status} to {self.state}")

    def apply_stop_result(self, result):
        """Modify the state according to the result. Raises ValueError or
        InvalidTransition on errors."""

        if (status := result.get("status")) is None:
            raise ValueError("Missing 'status' property")
        success_fail = ["success", "fail"]
        if self.state == self.State.STARTING and status in success_fail:
            self.state = self.State.STOPPED
        elif self.state == self.State.RUNNING and status in success_fail:
            self.state = self.State.STOPPED
        elif self.state == self.State.STOPPING and status in success_fail:
            self.state = self.State.STOPPED
        else:
            raise self.InvalidTransition(f"Apply stop result {status} to {self.state}")

    def __str__(self):
        return f"{self.task_type}: {self.state}"
