from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.views.generic.base import View
from rest_framework.authtoken.models import Token

from iot.forms import CreateControllerForm, CreateSiteForm
from iot.models import ControllerAuthToken, ControllerComponent, Site, SiteEntity
from iot.models.controller import ControllerComponentType


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
        return render(request, "iot/site_list.html", context)


class CreateSiteView(LoginRequiredMixin, View):
    """Allows a user to create a site"""

    def get(self, request, *args, **kwargs):
        return render(request, "iot/create_site.html", {"form": CreateSiteForm()})

    def post(self, request, *args, **kwargs):
        form = CreateSiteForm(request.POST)
        if form.is_valid():
            Site.objects.create(**form.cleaned_data, owner=request.user)
            return HttpResponseRedirect(reverse("iot:site-list"))
        return render(request, "iot/create_site.html", {"form": form}, status=400)


class DeleteSiteView(LoginRequiredMixin, View):
    """Allows a user to delete their sites"""

    def post(self, request, *args, **kwargs):
        Site.objects.filter(owner=request.user, pk=kwargs["pk"]).delete()
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
            site_entity = SiteEntity.objects.create(
                name=form.cleaned_data["name"], site=form.cleaned_data["site"]
            )
            if new_type_name := form.cleaned_data["new_type_name"]:
                controller_component_type = ControllerComponentType.objects.create(
                    name=new_type_name, created_by=request.user
                )
            else:
                controller_component_type = form.cleaned_data[
                    "controller_component_type"
                ]
            controller_component = ControllerComponent.objects.create(
                site_entity=site_entity, component_type=controller_component_type
            )
            ControllerAuthToken.objects.create(controller=controller_component)
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
        SiteEntity.objects.filter(site__owner=request.user, pk=kwargs["pk"]).delete()
        return HttpResponseRedirect(reverse("iot:controller-list"))


class CreateUserTokenView(LoginRequiredMixin, View):
    """Allows a user to create a user authentication token."""

    def post(self, request, *args, **kwargs):
        Token.objects.create(user=request.user, key=Token.generate_key())
        return HttpResponseRedirect(reverse("index"))


class DeleteUserTokenView(LoginRequiredMixin, View):
    """Allows a user to delete a user authentication token."""

    def post(self, request, *args, **kwargs):
        Token.objects.filter(user=request.user, key=kwargs["pk"]).delete()
        return HttpResponseRedirect(reverse("index"))