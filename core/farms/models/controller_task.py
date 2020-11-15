from typing import Dict, List, Type, Optional
import uuid
from datetime import datetime, timezone

from django.db import models, IntegrityError, transaction
from django.core.exceptions import ValidationError

from farms.models.controller import ControllerComponent


class ControllerTaskManager(models.Manager):
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
                state=self.model.STARTING_STATE,
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
            task.state = self.model.STOPPING_STATE
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
                task.state = ControllerTask.STARTING_STATE
            self.bulk_update(tasks, ["state"])

        commands = []
        for task in tasks:
            commands.append(task.to_start_command())
        if commands:
            return {"start": commands}
        return {}


class ControllerTask(models.Model):
    """Tasks interacting with peripherals on controllers"""

    objects = ControllerTaskManager()

    class InvalidTransition(Exception):
        """Thrown when an invalid state change is applied"""

    STARTING_STATE = "starting"
    RUNNING_STATE = "running"
    STOPPING_STATE = "stopping"
    FAILED_STATE = "failed"
    STOPPED_STATE = "stopped"

    # States for which stop commands can be created
    STOPPABLE_STATES = [STARTING_STATE, RUNNING_STATE, STOPPING_STATE]
    # States to start tasks again (registration after reboot)
    RE_START_STATES = [STARTING_STATE, RUNNING_STATE]

    STATE_CHOICES = [
        (STARTING_STATE, "Starting"),
        (RUNNING_STATE, "Running"),
        (STOPPING_STATE, "Stopping"),
        (FAILED_STATE, "Failed"),
        (STOPPED_STATE, "Stopped"),
    ]

    INVALID_TYPE = "InvalidTask"
    ALERT_SENSOR_TYPE = "AlertSensor"
    POLL_SENSOR_TYPE = "PollSensor"
    READ_SENSOR_TYPE = "ReadSensor"
    SET_LIGHT_TYPE = "SetLight"
    WRITE_ACTUATOR_TYPE = "WriteActuator"

    TYPE_CHOICES = [
        (INVALID_TYPE, "Invalid task"),
        (ALERT_SENSOR_TYPE, "Alert sensor"),
        (POLL_SENSOR_TYPE, "Poll sensor"),
        (READ_SENSOR_TYPE, "Read sensor"),
        (SET_LIGHT_TYPE, "Set light"),
        (WRITE_ACTUATOR_TYPE, "Write actuator"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    controller_component = models.ForeignKey(
        ControllerComponent,
        on_delete=models.CASCADE,
        help_text="On which controller this task is executed.",
    )
    task_type = models.CharField(
        choices=TYPE_CHOICES,
        max_length=64,
        help_text="The type of the task on the controller",
    )
    state = models.CharField(
        choices=STATE_CHOICES,
        max_length=64,
        help_text="The state of the controller task.",
    )
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="The construction parameters excl. UUID and type",
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

        if self.state == self.STARTING_STATE:
            if self.run_until:
                now = datetime.now(tz=timezone.utc)
                if self.run_until > now:
                    self.state = self.STOPPED_STATE
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

        if self.state == self.STOPPING_STATE:
            return {"uuid": str(self.id)}
        return None

    def apply_start_result(self, result):
        """Modify the state according to the result. Raises ValueError or
        InvalidTransition on errors."""

        try:
            status = result["status"]
        except KeyError as err:
            raise ValueError(f"Missing key {err}") from err
        if self.state == self.STARTING_STATE and status == "success":
            self.state = self.RUNNING_STATE
        elif self.state == self.STARTING_STATE and status == "fail":
            self.state = self.FAILED_STATE
        else:
            raise self.InvalidTransition(f"Apply start result {status} to {self.state}")

    def apply_stop_result(self, result):
        """Modify the state according to the result. Raises ValueError or
        InvalidTransition on errors."""

        if (status := result.get("status")) is None:
            raise ValueError("Missing 'status' property")
        success_fail = ["success", "fail"]
        if self.state == self.STARTING_STATE and status in success_fail:
            self.state = self.STOPPED_STATE
        elif self.state == self.RUNNING_STATE and status in success_fail:
            self.state = self.STOPPED_STATE
        elif self.state == self.STOPPING_STATE and status in success_fail:
            self.state = self.STOPPED_STATE
        else:
            raise self.InvalidTransition(f"Apply stop result {status} to {self.state}")

    def __str__(self):
        return f"{self.task_type}: {self.state}"
