from django.apps import AppConfig


class GreenhouseConfig(AppConfig):
    """App config for the greenhouse app."""

    name = 'greenhouse'

    def ready(self):
        import greenhouse.signals # pylint: disable=import-outside-toplevel
