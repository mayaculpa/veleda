# import uuid

# from celery import shared_task, current_task
# from celery.utils.log import get_task_logger
# import CloudFlare
# from django.core.exceptions import ValidationError, ObjectDoesNotExist
# from oauth2_provider.models import Application
# from django.conf import settings
# import sewer

# from .models import Site

# logger = get_task_logger(__name__)


# @shared_task
# def setup_subdomain_task(site_id: uuid):
#     # Check that the site has a valid subdomain and local IP address
#     site = Site.objects.select_related("coordinator").get(pk=site_id)
#     try:
#         if not site.subdomain or not site.coordinator.local_ip_address:
#             err = "Missing site/coordinator properties (site.id: {})".format(site_id)
#             logger.error(err)
#             raise ValidationError(err)
#     except ObjectDoesNotExist:
#         logger.error("Coordinator not linked to site (site.id: {})".format(site_id))
#         raise

#     logger.info("Creating subdomain: %s" % site.subdomain)
#     cf = CloudFlare.CloudFlare(token=settings.CLOUDFLARE_API_KEY)
#     # Get zones, to get the SERVER_DOMAIN's zone ID to create a subdomain DNS records
#     zone = cf.zones.get(params={"name": settings.SERVER_DOMAIN})[0]

#     # To split the subdomain correctly, the server domain has to be the first part
#     # I.e., some.sites.example.com --> 'some.sites' and 'example.com'
#     if zone["name"] not in site.subdomain:
#         raise ValidationError(
#             "Site subdomain is not part of the server domain ({})".format(
#                 site.subdomain, zone["name"]
#             )
#         )
#     subdomain_prefix = site.subdomain.split(zone["name"])[0][:-1]

#     # Create the new subdomain, if it exists retry and update the IP address
#     try:
#         dns_record = cf.zones.dns_records.post(
#             zone["id"],
#             data={
#                 "type": "A",
#                 "name": subdomain_prefix,
#                 "content": site.coordinator.local_ip_address,
#             },
#         )
#     except CloudFlare.exceptions.CloudFlareAPIError as err:
#         # If the subdomain exists (error code 82057), search for it's entry by name to
#         # get its ID and then update it's IP address
#         if int(err) == 81057:
#             dns_record = cf.zones.dns_records.get(
#                 zone["id"], params={"name": site.subdomain}
#             )[0]
#             if dns_record["content"] != site.coordinator.local_ip_address:
#                 dns_record = cf.zones.dns_records.put(
#                     zone["id"],
#                     dns_record["id"],
#                     data={
#                         "type": "A",
#                         "name": subdomain_prefix,
#                         "content": site.coordinator.local_ip_address,
#                     },
#                 )
#         else:
#             raise

#     logger.info("Creating OAuth2 credentials")
#     Application.objects.create(
#         user=site.owner,
#         redirect_uris=[site.subdomain],
#         client_type=Application.CLIENT_CONFIDENTIAL,
#         authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
#         name=site.name,
#         skip_authorization=True,
#     )

#     logger.info("Requesting Let's Encrypt certificate")
#     client = sewer.Client(domain_name=site.subdomain, dns_class=settings.DNS_PROVIDER)
#     certificate = client.cert()
#     certificate_key = client.certificate_key
#     account_key = client.account_key

