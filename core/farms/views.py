from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.views.generic.base import View
from ipware import get_client_ip

from .forms import (
    CreateSiteForm,
    CoordinatorSetupSelectForm,
    CoordinatorSetupRegistrationForm,
)
from .models import Site, Coordinator


class SiteListView(LoginRequiredMixin, View):
    """List of a user's site"""

    def get(self, request, *args, **kwargs):
        context = {}
        if "message" in kwargs:
            context["message"] = kwargs["message"]
        context["sites"] = Site.objects.filter(owner=request.user)
        return render(request, "farms/site_list.html", context=context)


class SiteSetupView(LoginRequiredMixin, View):
    """Allows a user to create a site"""

    def get(self, request, *args, **kwargs):
        return render(request, "farms/site_setup.html", {"form": CreateSiteForm()})

    def post(self, request, *args, **kwargs):
        form = CreateSiteForm(request.POST)

        if form.is_valid():
            Site.objects.create(**form.cleaned_data, owner=request.user)
            return HttpResponseRedirect(reverse("farms:site-list"))
        return render(request, "farms/site_setup.html", {"form": form}, status=400)


class CoordinatorSetupSelectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = {}

        client_ip, is_routable = get_client_ip(request)
        if not is_routable and not settings.DEBUG:
            context["error"] = (
                "Sorry, your external IP address can not be used for a lookup: %s"
                % client_ip
            )
            return render(
                request, "farms/coordinator_setup_select.html", context=context
            )

        coordinators = Coordinator.objects.filter(external_ip_address=client_ip)
        context["unregistered_coordinators"] = sorted(
            filter(lambda coordinator: not coordinator.site, coordinators),
            key=lambda coordinator: coordinator.modified_at,
        )
        context["registered_coordinators"] = sorted(
            filter(lambda coordinator: coordinator.site, coordinators),
            key=lambda coordinator: coordinator.modified_at,
        )
        return render(request, "farms/coordinator_setup_select.html", context=context)

    def post(self, request, *args, **kwargs):
        form = CoordinatorSetupSelectForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(
                reverse(
                    "farms:coordinator-setup-register",
                    kwargs={"pk": form.cleaned_data["coordinator_id"]},
                ),
            )

        return render(
            request, "farms/coordinator_setup_select.html", {"form": form}, status=400,
        )


class CoordinatorSetupRegisterView(LoginRequiredMixin, View):
    """The view to assign a coordinator to a site."""

    def get(self, request, *args, **kwargs):
        context = {}
        client_ip, is_routable = get_client_ip(request)
        if not is_routable and not settings.DEBUG:
            context["error"] = (
                "Sorry, your external IP address can not be used for a lookup: %s"
                % client_ip
            )
            return render(
                request, "farms/coordinator_setup_register.html", context=context
            )

        # Get all sites that do not have a coordinator
        sites = Site.objects.filter(coordinator__isnull=True).filter(owner=request.user)
        form = CoordinatorSetupRegistrationForm(sites=sites)
        return render(request, "farms/coordinator_setup_register.html", {"form": form},)

    def post(self, request, *args, **kwargs):
        sites = Site.objects.filter(coordinator__isnull=True).filter(owner=request.user)
        form = CoordinatorSetupRegistrationForm(request.POST, sites=sites)

        # Check if the request originates from a valid IP address
        client_ip, is_routable = get_client_ip(request)
        if not is_routable and not settings.DEBUG:
            form.add_error(
                None, "Your external IP address ({}) is not routable.".format(client_ip)
            )

        # Abort if the form is valid or any errors have been detected
        if not form.is_valid():
            return render(
                request, "farms/coordinator_setup_register.html", {"form": form},
            )

        # Abort if the request came from a different subnet
        coordinator = Coordinator.objects.get(id=kwargs["pk"])
        if client_ip != coordinator.external_ip_address:
            form.add_error(
                None,
                "Your external IP address ({}) does not match the coordinator's.".format(
                    client_ip
                ),
            )
            return render(
                request, "farms/coordinator_setup_register.html", {"form": form}
            )

        # Set the site and subdomain
        form.cleaned_data["site"].subdomain = (
            form.cleaned_data["subdomain_prefix"]
            + "."
            + settings.FARMS_SUBDOMAIN_NAMESPACE
            + "."
            + settings.SERVER_DOMAIN
        )
        form.cleaned_data["site"].save()
        coordinator.site = form.cleaned_data["site"]
        coordinator.save()
        # setup_subdomain_task.delay(coordinator.site.id)
        # TODO: Setup after registration
        # setup_subdomain_task.s(coordinator.site.id).apply()
        # messages.success(
        #     request, "Registration successful. Creating subdomain and credentials."
        # )
        return HttpResponseRedirect(reverse("site-list"))
