from typing import Dict, List, Type, Optional
import uuid

from django.db import models, IntegrityError

from farms.models.controller import ControllerComponent


class ControllerTaskManager(models.Manager):
    def from_commands(self, task_commands, controller) -> List[Type["ControllerTask"]]:
        """Parse a command message to create tasks and get those to be stopped"""

        tasks: List[Type["ControllerTask"]] = []
        if task_commands:
            create_commands = task_commands.get("create")
            if create_commands:
                tasks.extend(self.from_create_commands(create_commands, controller))
            stop_commands = task_commands.get("stop")
            if stop_commands:
                tasks.extend(self.from_stop_commands(stop_commands))
        return tasks

    def from_create_commands(
        self, create_commands: List[Dict], controller
    ) -> List[Type["ControllerTask"]]:
        """Create tasks from the task create command"""

        tasks: List[Type["ControllerTask"]] = []
        for create_command in create_commands:
            command = create_command.copy()
            try:
                task_id = command.pop("uuid")
                task_type = command.pop("type")
            except KeyError as err:
                if "task_id" in locals():
                    raise ValueError(f"Missing key {err} for {task_id}") from err
                raise ValueError(f"Missing key {err}") from err
            tasks.append(
                self.model(
                    id=task_id,
                    controller_component=controller,
                    state=self.model.STARTING_STATE,
                    task_type=task_type,
                    parameters=command,
                )
            )
        try:
            return self.bulk_create(tasks)
        except IntegrityError as err:
            raise ValueError(
                f"Integrity error: {str(err).split('DETAIL:  ',1)[1][:-1]}"
            ) from err

    def from_stop_commands(
        self, stop_commands: List[Dict]
    ) -> List[Type["ControllerTask"]]:
        """Request tasks to stop"""

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


class ControllerTask(models.Model):
    """Tasks interacting with peripherals on controllers"""

    objects = ControllerTaskManager()

    STARTING_STATE = "starting"
    RUNNING_STATE = "running"
    STOPPING_STATE = "stopping"
    FAILED_STATE = "failed"
    STOPPED_STATE = "stopped"

    STOPPABLE_STATES = [STARTING_STATE, RUNNING_STATE, STOPPING_STATE]

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
        help_text="The construction parameters excl. UUID and type"
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

        create_tasks = []
        stop_tasks = []
        for task in tasks:
            if task.state == cls.STARTING_STATE:
                create_tasks.append(task.to_create_command())
            if task.state == cls.STOPPING_STATE:
                stop_tasks.append(task.to_stop_command())

        commands = {}
        if create_tasks:
            commands.update({"create": create_tasks})
        if stop_tasks:
            commands.update({"stop": stop_tasks})
        return commands

    def to_create_command(self) -> Optional[Dict]:
        """If in starting state, return a command that creates the task, else None"""

        if self.state == self.STARTING_STATE:
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

    def __str__(self):
        return f"{self.task_type} "
