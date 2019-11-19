from django.shortcuts import render
from rest_framework import viewsets

from .models import Farm, Coordinator, HydroponicSystem, Controller
from .serializers import FarmSerializer, AddressSerializer CoordinatorSerializer, HydroponicSystemSerializer, ControllerSerializer
# Create your views here.

class FarmViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows farms to be viewed or edited.
    """
    queryset = Farm.objects.all().order_by('-date_created')
    serializer_class = FarmSerializer
