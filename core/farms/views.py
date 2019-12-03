from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, reverse
from django.views.generic.base import View
from django_celery_results.models import TaskResult
from ipware import get_client_ip
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import (
    CreateFarmForm,
    CoordinatorSetupSelectForm,
    CoordinatorSetupRegistrationForm,
)
from .models import Farm, Coordinator, HydroponicSystem, Controller
from .tasks import setup_subdomain_task
from .serializers import (
    AddressSerializer,
    CoordinatorPingSerializer,
    CoordinatorSerializer,
    ControllerSerializer,
    FarmSerializer,
    HydroponicSystemSerializer,
)


class FarmDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pass


class FarmListView(LoginRequiredMixin, View):
    """List of a user's farm"""

    def get(self, request, *args, **kwargs):
        context = {}
        if "message" in kwargs:
            context["message"] = kwargs["message"]
        context["farms"] = Farm.objects.filter(owner=request.user)
        return render(request, "farms/farm_list.html", context=context)


class FarmSetupView(LoginRequiredMixin, View):
    """Allows a user to create a farm"""

    def get(self, request, *args, **kwargs):
        return render(request, "farms/farm_setup.html", {"form": CreateFarmForm()})

    def post(self, request, *args, **kwargs):
        form = CreateFarmForm(request.POST)

        if form.is_valid():
            Farm.objects.create(**form.cleaned_data, owner=request.user)
            return HttpResponseRedirect(reverse("farm-list"))
        else:
            return render(request, "farms/farm_setup.html", {"form": form}, status=400)


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
            filter(lambda coordinator: not coordinator.farm, coordinators),
            key=lambda coordinator: coordinator.modified_at,
        )
        context["registered_coordinators"] = sorted(
            filter(lambda coordinator: coordinator.farm, coordinators),
            key=lambda coordinator: coordinator.modified_at,
        )
        return render(request, "farms/coordinator_setup_select.html", context=context)

    def post(self, request, *args, **kwargs):
        form = CoordinatorSetupSelectForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(
                reverse(
                    "coordinator-setup-register",
                    kwargs={"pk": form.cleaned_data["coordinator_id"]},
                ),
            )
        else:
            return render(
                request,
                "farms/coordinator_setup_select.html",
                {"form": form},
                status=400,
            )


class CoordinatorSetupRegisterView(LoginRequiredMixin, View):
    """The view to assign a coordinator to a farm."""

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

        # Get all farms that do not have a coordinator
        farms = Farm.objects.filter(coordinator__isnull=True).filter(owner=request.user)
        form = CoordinatorSetupRegistrationForm(farms=farms)
        return render(request, "farms/coordinator_setup_register.html", {"form": form},)

    def post(self, request, *args, **kwargs):
        farms = Farm.objects.filter(coordinator__isnull=True).filter(owner=request.user)
        form = CoordinatorSetupRegistrationForm(request.POST, farms=farms)

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

        # Set the farm and subdomain
        form.cleaned_data["farm"].subdomain = form.cleaned_data["subdomain_prefix"] + "." + settings.FARMS_SUBDOMAIN_NAMESPACE + "." + settings.SERVER_DOMAIN
        form.cleaned_data["farm"].save()
        coordinator.farm = form.cleaned_data["farm"]
        coordinator.save()
        # setup_subdomain_task.delay(coordinator.farm.id)
        setup_subdomain_task.s(coordinator.farm.id).apply()
        messages.success(request, 'Registration successful. Creating subdomain and credentials.')        
        return HttpResponseRedirect(reverse("farm-list"))


class CoordinatorPingView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # Find the external IP address from the request
        # TODO: Handle IPv6 properly: http://www.steves-internet-guide.com/ipv6-guide/
        client_ip, is_routable = get_client_ip(request)
        if not is_routable and not settings.DEBUG:
            error_msg = "External IP address is not routable: %s" % client_ip
            return JsonResponse(data={"error": error_msg}, status=400)
        else:
            data = request.data.copy()
            data["external_ip_address"] = client_ip

        # Serialize the request
        serializer = CoordinatorPingSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400)

        # If the coordinator has been registered, only allow authenticated view
        try:
            coordinator = Coordinator.objects.get(pk=serializer.validated_data["id"])
            if coordinator.farm:
                coordinator_url = CoordinatorSerializer(
                    coordinator, context={"request": request}
                ).data["url"]
                error_msg = (
                    "Coordinator has been registered. Use the detail URL: %s"
                    % coordinator_url
                )
                return JsonResponse(data={"error": error_msg}, status=403)
        except ObjectDoesNotExist:
            pass

        serializer.save()
        return JsonResponse(serializer.data, status=201)


class CoordinatorDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pass

