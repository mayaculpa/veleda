from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.views.generic.base import View
from django.db.utils import IntegrityError
from rest_framework.authtoken.models import Token

from iot.forms import CreateControllerForm, CreateSiteForm
from iot.models import ControllerComponent, Site, SiteEntity


class SiteListView(LoginRequiredMixin, View):
    """List of a user's site"""

    def get(self, request, *args, **kwargs):
        context = {}
        context["sites"] = (
            Site.objects.filter(owner=request.user)
            .annotate(num_entities=Count("site_entity"))
            .annotate(num_controllers=Count("site_entity__controller_component"))
            .order_by("-num_entities")
        )
        context["controller_count"] = ControllerComponent.objects.filter(
            site_entity__site__owner=request.user
        ).count()
        return render(request, "iot/site_list.html", context)


class CreateSiteView(LoginRequiredMixin, View):
    """Allows a user to create a site"""

    def get(self, request, *args, **kwargs):
        return render(request, "iot/create_site.html", {"form": CreateSiteForm()})

    def post(self, request, *args, **kwargs):
        form = CreateSiteForm(request.POST)
        if form.is_valid():
            site = Site.objects.create(**form.cleaned_data, owner=request.user)
            messages.success(request, f"Created site {site.name}")
            return HttpResponseRedirect(reverse("iot:site-list"))
        return render(request, "iot/create_site.html", {"form": form}, status=400)


class DeleteSiteView(LoginRequiredMixin, View):
    """Allows a user to delete their sites"""

    def post(self, request, *args, **kwargs):
        try:
            site = Site.objects.filter(owner=request.user).get(pk=kwargs["pk"])
            site.delete()
            messages.success(request, f"Deleted site {site.name}")
        except Site.DoesNotExist:
            messages.error(request, f"Failed deleting site")
        return HttpResponseRedirect(reverse("iot:site-list"))


class ControllerListView(LoginRequiredMixin, View):
    """List of a user's controllers"""

    def get(self, request, *args, **kwargs):
        context = {}
        context["controllers"] = (
            ControllerComponent.objects.select_related(
                "site_entity", "site_entity__site", "auth_token", "component_type"
            )
            .filter(site_entity__site__owner=request.user)
            .annotate(num_peripherals=Count("peripheral_component_set"))
        )
        return render(request, "iot/controller_list.html", context)


class CreateControllerView(LoginRequiredMixin, View):
    """Allows a user to create and register a controller"""

    def get(self, request, *args, **kwargs):
        form = CreateControllerForm(request.user)
        context = {
            "sites": form.fields["site"].queryset,
            "controller_component_types": form.fields[
                "controller_component_type"
            ].queryset,
        }
        return render(request, "iot/create_controller.html", context)

    def post(self, request, *args, **kwargs):
        form = CreateControllerForm(request.user, request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            site = form.cleaned_data.get("site")
            type_name = form.cleaned_data.get("new_type_name")
            controller_type = form.cleaned_data.get("controller_component_type")
            if type_name:
                controller = (
                    ControllerComponent.objects.create_controller_with_new_type(
                        name=name, site=site, type_name=type_name
                    )
                )
            else:
                controller = ControllerComponent.objects.create_controller(
                    name=name, site=site, controller_component_type=controller_type
                )
            name = controller.site_entity.name
            messages.success(request, f"Successfully created controller {name}")
            return HttpResponseRedirect(reverse("iot:controller-list"))
        context = {
            "form": form,
            "sites": form.fields["site"].queryset,
            "controller_component_types": form.fields[
                "controller_component_type"
            ].queryset,
        }
        return render(request, "iot/create_controller.html", context, status=400)


class DeleteControllerView(LoginRequiredMixin, View):
    """Allows a user to delete their controllers"""

    def post(self, request, *args, **kwargs):
        """Try to delete controller if it exists and belongs to user"""

        try:
            site_entity = SiteEntity.objects.filter(site__owner=request.user).get(
                pk=kwargs["pk"]
            )
            site_entity.delete()
            messages.success(request, f"Deleted controller {site_entity.name}")
        except SiteEntity.DoesNotExist:
            messages.error(request, "Failed to delete controller")
        return HttpResponseRedirect(reverse("iot:controller-list"))


class CreateUserTokenView(LoginRequiredMixin, View):
    """Allows a user to create a user authentication token."""

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                Token.objects.create(user=request.user, key=Token.generate_key())
            messages.success(request, "Created user authentication token")
        except IntegrityError:
            Token.objects.filter(user=request.user).delete()
            Token.objects.create(user=request.user, key=Token.generate_key())
            messages.success(request, "Replaced user authentication token")
        return HttpResponseRedirect(reverse("index"))


class DeleteUserTokenView(LoginRequiredMixin, View):
    """Allows a user to delete a user authentication token."""

    def post(self, request, *args, **kwargs):
        count, _ = Token.objects.filter(user=request.user).delete()
        if count:
            messages.success(request, "Deleted authentication token")
        else:
            messages.error(request, "No authentication token found")
        return HttpResponseRedirect(reverse("index"))