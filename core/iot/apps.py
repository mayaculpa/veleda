from django.apps import AppConfig


class IotConfig(AppConfig):
    name = "iot"

    def ready(self):
        import iot.signals # pylint: disable=import-outside-toplevel, unused-import
