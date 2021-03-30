from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class PrivateMediaStorage(S3Boto3Storage):
    """Extend S3 with signed URLs for custom domains."""
    
    custom_domain = False

    def url(self, name, parameters=None, expire=None, http_method=None):
        """Replace internal domain with custom domain for signed URLs."""
        url = super().url(name, parameters, expire, http_method)
        custom_url = url.replace(
            settings.AWS_S3_ENDPOINT_URL,
            f"{settings.AWS_S3_URL_PROTOCOL}//{settings.AWS_S3_CUSTOM_DOMAIN}",
        )
        return custom_url
