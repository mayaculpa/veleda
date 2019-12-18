# import uuid

# from celery import shared_task, current_task
# from celery.utils.log import get_task_logger
# import CloudFlare
# from django.core.exceptions import ValidationError, ObjectDoesNotExist
# from oauth2_provider.models import Application
# from django.conf import settings
# import sewer

# from .models import Farm

# logger = get_task_logger(__name__)


# @shared_task
# def setup_subdomain_task(farm_id: uuid):
#     # Check that the farm has a valid subdomain and local IP address
#     farm = Farm.objects.select_related("coordinator").get(pk=farm_id)
#     try:
#         if not farm.subdomain or not farm.coordinator.local_ip_address:
#             err = "Missing farm/coordinator properties (farm.id: {})".format(farm_id)
#             logger.error(err)
#             raise ValidationError(err)
#     except ObjectDoesNotExist:
#         logger.error("Coordinator not linked to farm (farm.id: {})".format(farm_id))
#         raise

#     logger.info("Creating subdomain: %s" % farm.subdomain)
#     cf = CloudFlare.CloudFlare(token=settings.CLOUDFLARE_API_KEY)
#     # Get zones, to get the SERVER_DOMAIN's zone ID to create a subdomain DNS records
#     zone = cf.zones.get(params={"name": settings.SERVER_DOMAIN})[0]

#     # To split the subdomain correctly, the server domain has to be the first part
#     # I.e., some.farms.example.com --> 'some.farms' and 'example.com'
#     if zone["name"] not in farm.subdomain:
#         raise ValidationError(
#             "Farm subdomain is not part of the server domain ({})".format(
#                 farm.subdomain, zone["name"]
#             )
#         )
#     subdomain_prefix = farm.subdomain.split(zone["name"])[0][:-1]

#     # Create the new subdomain, if it exists retry and update the IP address
#     try:
#         dns_record = cf.zones.dns_records.post(
#             zone["id"],
#             data={
#                 "type": "A",
#                 "name": subdomain_prefix,
#                 "content": farm.coordinator.local_ip_address,
#             },
#         )
#     except CloudFlare.exceptions.CloudFlareAPIError as err:
#         # If the subdomain exists (error code 82057), search for it's entry by name to
#         # get its ID and then update it's IP address
#         if int(err) == 81057:
#             dns_record = cf.zones.dns_records.get(
#                 zone["id"], params={"name": farm.subdomain}
#             )[0]
#             if dns_record["content"] != farm.coordinator.local_ip_address:
#                 dns_record = cf.zones.dns_records.put(
#                     zone["id"],
#                     dns_record["id"],
#                     data={
#                         "type": "A",
#                         "name": subdomain_prefix,
#                         "content": farm.coordinator.local_ip_address,
#                     },
#                 )
#         else:
#             raise

#     logger.info("Creating OAuth2 credentials")
#     Application.objects.create(
#         user=farm.owner,
#         redirect_uris=[farm.subdomain],
#         client_type=Application.CLIENT_CONFIDENTIAL,
#         authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
#         name=farm.name,
#         skip_authorization=True,
#     )

#     logger.info("Requesting Let's Encrypt certificate")
#     client = sewer.Client(domain_name=farm.subdomain, dns_class=settings.DNS_PROVIDER)
#     certificate = client.cert()
#     certificate_key = client.certificate_key
#     account_key = client.account_key

