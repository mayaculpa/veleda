from django.apps import AppConfig


class FarmsConfig(AppConfig):
    name = "farms"

    def ready(self):
        import farms.signals  # pylint: disable=unused-import, import-outside-toplevel
